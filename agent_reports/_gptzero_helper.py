"""GPTZero scoring helper. Reads key from ~/.gptzero_key, posts to /v2/predict/text."""
import os, sys, json, time, urllib.request, urllib.error

KEY_PATH = os.path.expanduser('~/.gptzero_key')
with open(KEY_PATH) as f:
    KEY = f.read().strip()

URL = 'https://api.gptzero.me/v2/predict/text'


def score(text, retries=3):
    if len(text) < 300:
        raise ValueError(f"text must be >=300 chars, got {len(text)}")
    body = json.dumps({"document": text}).encode('utf-8')
    req = urllib.request.Request(URL, data=body, headers={
        'Content-Type': 'application/json',
        'x-api-key': KEY,
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    }, method='POST')
    last = None
    for i in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')}"
        except Exception as e:
            last = f"ERR: {e}"
        time.sleep(2 + i*2)
    raise RuntimeError(f"gptzero failed: {last}")


def summary(resp):
    # GPTZero schema: documents[0].class_probabilities and .predicted_class
    try:
        d = resp.get('documents', [resp])[0]
        cp = d.get('class_probabilities') or d.get('classProbabilities') or {}
        pc = d.get('predicted_class') or d.get('predictedClass')
        return {
            'p_ai': cp.get('ai'),
            'p_human': cp.get('human'),
            'p_mixed': cp.get('mixed'),
            'predicted_class': pc,
        }
    except Exception as e:
        return {'error': str(e), 'raw_keys': list(resp.keys())}


if __name__ == '__main__':
    # quick: score a text from stdin or file
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            text = f.read()
    else:
        text = sys.stdin.read()
    r = score(text)
    print(json.dumps(summary(r), indent=2))
