// SPDX-License-Identifier: MIT
// peach-admin runs as CGI under QTS, never as a public standalone server.
package main

import (
	"bytes"
	"context"
	"crypto/hmac"
	"crypto/sha256"
	"crypto/tls"
	_ "embed"
	"encoding/hex"
	"encoding/json"
	"encoding/xml"
	"errors"
	"fmt"
	"html/template"
	"io"
	"net"
	"net/http"

	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"time"
	"unicode/utf8"
)

//go:embed password.py
var passwordProgram string

const adminPath = "/cgi-bin/peach-qnap.cgi"

type app struct {
	authorize func(*http.Request) (string, error)
	save      func(context.Context, string, string) error
	port      string
}

type authReply struct {
	Passed int `xml:"authPassed"`
	Admin  int `xml:"isAdmin"`
}

func setting(section, key, fallback, file string) string {
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	out, err := exec.CommandContext(ctx, "/sbin/getcfg", section, key, "-d", fallback, "-f", file).Output()
	if err != nil {
		return fallback
	}
	return strings.TrimSpace(string(out))
}
func validPort(s string) bool { n, err := strconv.Atoi(s); return err == nil && n > 0 && n <= 65535 }

// Only a fixed loopback destination is contacted. Redirects and environment
// proxies are disabled, so QTS session credentials cannot leave this NAS.
func qtsClient() *http.Client {
	return &http.Client{Timeout: 5 * time.Second, Transport: &http.Transport{
		Proxy:           nil,
		TLSClientConfig: &tls.Config{InsecureSkipVerify: true, MinVersion: tls.VersionTLS12}, // QTS loopback uses its local/self-signed certificate.
	}, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
}

func credentials(r *http.Request) (url.Values, string, error) {
	// QTS can use either session cookie. Prefer qtoken like its supported clients.
	if t, err := r.Cookie("qtoken"); err == nil && t.Value != "" && len(t.Value) <= 4096 {
		u, err := r.Cookie("NAS_USER")
		if err == nil && u.Value != "" && len(u.Value) <= 256 {
			return url.Values{"qtoken": {t.Value}, "user": {u.Value}}, "qtoken:" + u.Value + ":" + t.Value, nil
		}
	}
	if s, err := r.Cookie("NAS_SID"); err == nil && s.Value != "" && len(s.Value) <= 4096 {
		return url.Values{"sid": {s.Value}}, "sid:" + s.Value, nil
	}
	return nil, "", errors.New("QTS session missing")
}
func authorizeQTS(r *http.Request) (string, error) {
	query, key, err := credentials(r)
	if err != nil {
		return "", err
	}
	httpPort := setting("System", "Web Access Port", "8080", "/etc/config/uLinux.conf")
	httpsPort := setting("System", "SSL Port", "443", "/etc/config/uLinux.conf")
	client := qtsClient()
	for _, endpoint := range []struct{ scheme, port string }{{"https", httpsPort}, {"http", httpPort}} {
		if !validPort(endpoint.port) {
			continue
		}
		target := endpoint.scheme + "://127.0.0.1:" + endpoint.port + "/cgi-bin/authLogin.cgi?" + query.Encode()
		req, err := http.NewRequestWithContext(r.Context(), http.MethodGet, target, nil)
		if err != nil {
			continue
		}
		resp, err := client.Do(req)
		if err != nil {
			continue
		}
		approved := administratorResponse(resp)
		resp.Body.Close()
		if approved {
			return key, nil
		}
	}
	return "", errors.New("QTS administrator verification failed")
}

func administratorResponse(resp *http.Response) bool {
	var reply authReply
	err := xml.NewDecoder(io.LimitReader(resp.Body, 65536)).Decode(&reply)
	return resp.StatusCode == 200 && err == nil && reply.Passed == 1 && reply.Admin == 1
}

func csrf(key string) string {
	mac := hmac.New(sha256.New, []byte(key))
	mac.Write([]byte("PeachQNAP password form v1:" + adminPath))
	return hex.EncodeToString(mac.Sum(nil))
}
func sameOrigin(r *http.Request) bool {
	origin, err := url.Parse(r.Header.Get("Origin"))
	if err != nil || origin.Host != r.Host || origin.User != nil || origin.RawQuery != "" || origin.Fragment != "" || origin.Path != "" {
		return false
	}
	scheme := "http"
	if r.TLS != nil {
		scheme = "https"
	}
	return origin.Scheme == scheme
}
func serviceURL(host, port string) string {
	if h, _, err := net.SplitHostPort(host); err == nil {
		host = h
	}
	host = strings.Trim(host, "[]")
	return (&url.URL{Scheme: "http", Host: net.JoinHostPort(host, port), Path: "/"}).String()
}

var page = template.Must(template.New("page").Parse(`<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Peach · 访问设置</title><style>body{font:16px system-ui;background:#faf8f5;color:#282624;margin:0;padding:40px 20px}main{max-width:480px;margin:3vh auto;background:white;padding:32px;border-radius:20px;border:1px solid #e9e3de}h1{font-size:26px}p{line-height:1.7}label{display:block;margin:18px 0 6px}input{box-sizing:border-box;width:100%;padding:12px;border:1px solid #bbb;border-radius:8px;font:inherit}button,a{display:inline-block;margin:20px 8px 0 0;padding:12px 18px;border-radius:9px}button{background:#a63b33;color:white;border:0;font:inherit;cursor:pointer}a{color:#92372e}.notice{padding:12px;background:#f7f1e9;border-radius:8px}</style><main><h1>🍑 Peach 访问设置</h1><p>已验证 QTS 管理员身份。你可以在这里设置或重置 Peach 的访问密码，无需 SSH。</p>{{if .Message}}<p class="notice" role="status">{{.Message}}</p>{{end}}<form method="post" action="/cgi-bin/peach-qnap.cgi"><input type="hidden" name="csrf" value="{{.CSRF}}"><label for="password">新的访问密码</label><input id="password" name="password" type="password" autocomplete="new-password" minlength="8" maxlength="256" required><label for="confirmation">再次输入密码</label><input id="confirmation" name="confirmation" type="password" autocomplete="new-password" minlength="8" maxlength="256" required><p>保存会替换现有密码，其他浏览器需要重新登录。不会修改影片或馆藏数据。</p><button type="submit">保存密码</button><a href="{{.URL}}" rel="noreferrer">进入 Peach →</a></form></main></html>`))

func (a app) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Cache-Control", "no-store")
	w.Header().Set("Referrer-Policy", "no-referrer")
	w.Header().Set("X-Frame-Options", "DENY")
	w.Header().Set("X-Content-Type-Options", "nosniff")
	w.Header().Set("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
	if r.Method != "GET" && r.Method != "POST" {
		http.Error(w, "Method not allowed", 405)
		return
	}
	key, err := a.authorize(r)
	if err != nil {
		http.Error(w, "请先在同一浏览器登录 QTS 管理员账号，再从 App Center 打开 Peach。未能验证管理员会话，密码未更改。", 403)
		return
	}
	message := ""
	status := 200
	if r.Method == "POST" {
		if !sameOrigin(r) {
			http.Error(w, "请从本页面提交密码。", 403)
			return
		}
		r.Body = http.MaxBytesReader(w, r.Body, 8192)
		if err := r.ParseForm(); err != nil {
			http.Error(w, "Invalid form", 400)
			return
		}
		if !hmac.Equal([]byte(r.PostForm.Get("csrf")), []byte(csrf(key))) {
			http.Error(w, "请刷新页面后重试。", 403)
			return
		}
		password, confirmation := r.PostForm.Get("password"), r.PostForm.Get("confirmation")
		n := utf8.RuneCountInString(password)
		if !utf8.ValidString(password) || n < 8 || n > 256 || password != confirmation {
			status, message = 400, "密码需为 8–256 个字符，且两次输入一致。"
		} else if err := a.save(r.Context(), password, confirmation); err != nil {
			status, message = 503, "保存失败。请确认 Container Station 中 peach-qnap 正在运行，再重试。原密码可能已保存，请先尝试登录。"
		} else {
			message = "密码已保存。点击「进入 Peach」，使用新密码登录。"
		}
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	w.WriteHeader(status)
	// Passwords, QTS cookies and command output never enter responses or logs.
	_ = page.Execute(w, struct{ Message, CSRF, URL string }{message, csrf(key), serviceURL(r.Host, a.port)})
}

func savePassword(ctx context.Context, password, confirmation string) error {
	cs := setting("container-station", "Install_Path", "", "/etc/config/qpkg.conf")
	if !filepath.IsAbs(cs) {
		return errors.New("Container Station missing")
	}
	ctx, cancel := context.WithTimeout(ctx, 15*time.Second)
	defer cancel()
	docker := filepath.Join(cs, "bin/docker")
	check := exec.CommandContext(ctx, docker, "container", "inspect", "--format", `{{index .Config.Labels "io.peach.qnap.owner"}}`, "peach-qnap")
	label, err := check.Output()
	if err != nil || strings.TrimSpace(string(label)) != "PeachQNAP" {
		return errors.New("container ownership mismatch")
	}
	body, err := json.Marshal(map[string]string{"password": password, "confirmation": confirmation})
	if err != nil {
		return err
	}
	cmd := exec.CommandContext(ctx, docker, "exec", "-i", "peach-qnap", "python", "-c", passwordProgram)
	cmd.Stdin = bytes.NewReader(body)
	cmd.Stdout, cmd.Stderr = io.Discard, io.Discard
	return cmd.Run()
}
func main() {
	root := setting("PeachQNAP", "Install_Path", "", "/etc/config/qpkg.conf")
	if !filepath.IsAbs(root) {
		fmt.Print("Status: 503 Service Unavailable\r\nContent-Type: text/plain\r\n\r\nPeach installation unavailable")
		return
	}
	port := setting("PeachQNAP", "Port", "8900", filepath.Join(root, "peach-qnap.conf"))
	if !validPort(port) {
		port = "8900"
	}
	if err := serveCGI(app{authorize: authorizeQTS, save: savePassword, port: port}); err != nil {
		os.Exit(1)
	}
}

// Minimal CGI adapter: accept only the fields used by this bounded form handler.
func serveCGI(handler http.Handler) error {
	scheme := "http"
	secure := strings.EqualFold(os.Getenv("HTTPS"), "on") || os.Getenv("HTTPS") == "1"
	if secure {
		scheme = "https"
	}
	host := os.Getenv("HTTP_HOST")
	if host == "" {
		return errors.New("CGI host missing")
	}
	length := int64(0)
	if raw := os.Getenv("CONTENT_LENGTH"); raw != "" {
		var err error
		length, err = strconv.ParseInt(raw, 10, 64)
		if err != nil || length < 0 || length > 8192 {
			_, err = io.WriteString(os.Stdout, "Status: 413 Content Too Large\r\nContent-Type: text/plain\r\n\r\nForm too large")
			return err
		}
	}
	req, err := http.NewRequest(os.Getenv("REQUEST_METHOD"), scheme+"://"+host+adminPath, io.LimitReader(os.Stdin, length))
	if err != nil {
		return err
	}
	req.Header.Set("Cookie", os.Getenv("HTTP_COOKIE"))
	req.Header.Set("Origin", os.Getenv("HTTP_ORIGIN"))
	req.Header.Set("Content-Type", os.Getenv("CONTENT_TYPE"))
	if secure {
		req.TLS = &tls.ConnectionState{}
	}
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	response := &cgiResponse{header: make(http.Header)}
	handler.ServeHTTP(response, req.WithContext(ctx))
	if response.status == 0 {
		response.status = 200
	}
	if _, err := fmt.Fprintf(os.Stdout, "Status: %d %s\r\n", response.status, http.StatusText(response.status)); err != nil {
		return err
	}
	if err := response.header.Write(os.Stdout); err != nil {
		return err
	}
	if _, err := io.WriteString(os.Stdout, "\r\n"); err != nil {
		return err
	}
	_, err = response.body.WriteTo(os.Stdout)
	return err
}

type cgiResponse struct {
	header http.Header
	body   bytes.Buffer
	status int
}

func (w *cgiResponse) Header() http.Header { return w.header }
func (w *cgiResponse) WriteHeader(status int) {
	if w.status == 0 {
		w.status = status
	}
}
func (w *cgiResponse) Write(data []byte) (int, error) {
	if w.status == 0 {
		w.status = 200
	}
	return w.body.Write(data)
}
