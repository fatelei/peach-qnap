package main

import (
	"context"
	"errors"
	"io"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"testing"
)

func TestPasswordBoundary(t *testing.T) {
	for _, tc := range []struct {
		name, key, origin, token, password, confirm string
		denied                                      bool
		status, saves                               int
	}{
		{"valid", "session", "http://nas:5000", csrf("session"), "Test-secret-7821", "Test-secret-7821", false, 200, 1},
		{"unauthenticated", "", "http://nas:5000", "", "Test-secret-7821", "Test-secret-7821", true, 403, 0},
		{"other origin", "session", "http://evil.example", csrf("session"), "Test-secret-7821", "Test-secret-7821", false, 403, 0},
		{"null origin", "session", "null", csrf("session"), "Test-secret-7821", "Test-secret-7821", false, 403, 0},
		{"no origin valid csrf", "session", "", csrf("session"), "Test-secret-7821", "Test-secret-7821", false, 200, 1},
		{"no origin wrong csrf", "session", "", csrf("other-session"), "Test-secret-7821", "Test-secret-7821", false, 403, 0},
		{"no origin missing csrf", "session", "", "", "Test-secret-7821", "Test-secret-7821", false, 403, 0},
		{"no origin unauthenticated", "", "", "", "Test-secret-7821", "Test-secret-7821", true, 403, 0},
		{"wrong csrf", "session", "http://nas:5000", csrf("other-session"), "Test-secret-7821", "Test-secret-7821", false, 403, 0},
		{"short", "session", "http://nas:5000", csrf("session"), "short", "short", false, 400, 0},
		{"mismatch", "session", "http://nas:5000", csrf("session"), "Test-secret-7821", "different", false, 400, 0},
	} {
		t.Run(tc.name, func(t *testing.T) {
			calls := 0
			a := app{port: "8900", authorize: func(*http.Request) (string, error) {
				if tc.denied {
					return "", errors.New("no")
				}
				return tc.key, nil
			}, save: func(_ context.Context, p, c string) error {
				calls++
				if p != tc.password || c != tc.confirm {
					t.Fatal("wrong input")
				}
				return nil
			}}
			form := url.Values{"csrf": {tc.token}, "password": {tc.password}, "confirmation": {tc.confirm}}
			r := httptest.NewRequest("POST", "http://nas:5000"+adminPath, strings.NewReader(form.Encode()))
			r.Header.Set("Content-Type", "application/x-www-form-urlencoded")
			r.Header.Set("Origin", tc.origin)
			w := httptest.NewRecorder()
			a.ServeHTTP(w, r)
			if w.Code != tc.status || calls != tc.saves {
				t.Fatalf("status=%d calls=%d", w.Code, calls)
			}
			if strings.Contains(w.Body.String(), tc.password) {
				t.Fatal("password echoed")
			}
			if w.Header().Get("Cache-Control") != "no-store" {
				t.Fatal("response cacheable")
			}
		})
	}
}
func TestPageDoesNotWriteOrExposeSession(t *testing.T) {
	a := app{port: "8900", authorize: func(*http.Request) (string, error) { return "private-session-value", nil }, save: func(context.Context, string, string) error { t.Fatal("GET changed password"); return nil }}
	w := httptest.NewRecorder()
	a.ServeHTTP(w, httptest.NewRequest("GET", "http://nas:5000"+adminPath, nil))
	if w.Code != 200 || strings.Contains(w.Body.String(), "private-session-value") {
		t.Fatal(w.Body.String())
	}
	if got := w.Header().Get("Referrer-Policy"); got != "same-origin" {
		t.Fatalf("form policy %q turns browser POST Origin into null; want same-origin", got)
	}
	if !strings.Contains(w.Body.String(), "http://nas:8900/") {
		t.Fatal("missing Peach link")
	}
}
func TestBackendErrorDoesNotLeak(t *testing.T) {
	a := app{port: "8900", authorize: func(*http.Request) (string, error) { return "session", nil }, save: func(context.Context, string, string) error { return errors.New("SECRET") }}
	r := httptest.NewRequest("POST", "http://nas:5000"+adminPath, strings.NewReader(url.Values{"csrf": {csrf("session")}, "password": {"some-password"}, "confirmation": {"some-password"}}.Encode()))
	r.Header.Set("Origin", "http://nas:5000")
	r.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	w := httptest.NewRecorder()
	a.ServeHTTP(w, r)
	if w.Code != 503 || strings.Contains(w.Body.String(), "SECRET") {
		t.Fatal(w.Body.String())
	}
}
func TestNoRedirectOrProxy(t *testing.T) {
	client := qtsClient()
	if client.Transport.(*http.Transport).Proxy != nil {
		t.Fatal("proxy enabled")
	}
	destination := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { t.Error("followed redirect") }))
	defer destination.Close()
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { http.Redirect(w, r, destination.URL, 302) }))
	defer server.Close()
	resp, err := client.Get(server.URL)
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	io.Copy(io.Discard, resp.Body)
	if resp.StatusCode != 302 {
		t.Fatal(resp.StatusCode)
	}
}
func TestCredentialSources(t *testing.T) {
	r := httptest.NewRequest("GET", "http://nas/", nil)
	if _, _, err := credentials(r); err == nil {
		t.Fatal("accepted no cookies")
	}
	r.AddCookie(&http.Cookie{Name: "NAS_SID", Value: "sid-value"})
	q, _, err := credentials(r)
	if err != nil || q.Get("sid") != "sid-value" {
		t.Fatal("sid rejected")
	}
	r.AddCookie(&http.Cookie{Name: "qtoken", Value: "token-value"})
	r.AddCookie(&http.Cookie{Name: "NAS_USER", Value: "admin"})
	q, _, err = credentials(r)
	if err != nil || q.Get("qtoken") != "token-value" || q.Get("user") != "admin" {
		t.Fatal("qtoken rejected")
	}
}

func TestAdminResponse(t *testing.T) {
	for _, tc := range []struct {
		body   string
		status int
		want   bool
	}{
		{"<QDocRoot><authPassed>1</authPassed><isAdmin>1</isAdmin></QDocRoot>", 200, true},
		{"<QDocRoot><authPassed>1</authPassed><isAdmin>0</isAdmin></QDocRoot>", 200, false},
		{"<QDocRoot><authPassed>0</authPassed><isAdmin>1</isAdmin></QDocRoot>", 200, false},
		{"<QDocRoot><authPassed>1</authPassed><isAdmin>1</isAdmin></QDocRoot>", 403, false},
		{"<QDocRoot><isAdmin>1</isAdmin></QDocRoot>", 200, false},
		{"<invalid", 200, false},
	} {
		resp := &http.Response{StatusCode: tc.status, Body: io.NopCloser(strings.NewReader(tc.body))}
		if got := administratorResponse(resp); got != tc.want {
			t.Errorf("%s: got %v", tc.body, got)
		}
	}
}
