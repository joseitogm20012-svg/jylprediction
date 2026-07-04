import os
import requests

BASE_URL = os.environ.get("TARGET_URL", "http://localhost:3005")

def test_index_html():
    resp = requests.get(f"{BASE_URL}/", timeout=10)
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")

def test_style_css():
    resp = requests.get(f"{BASE_URL}/style.css", timeout=10)
    assert resp.status_code == 200
    assert "text/css" in resp.headers.get("content-type", "")

def test_script_js():
    resp = requests.get(f"{BASE_URL}/script.js", timeout=10)
    assert resp.status_code == 200
    assert "javascript" in resp.headers.get("content-type", "")

if __name__ == "__main__":
    test_index_html()
    test_style_css()
    test_script_js()
    print("TC009 PASSED")
