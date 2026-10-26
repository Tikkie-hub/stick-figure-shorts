"""Open the local studio after its HTTP server is ready, without a console race."""
import time
import urllib.error
import urllib.request
import webbrowser


def main():
    address = 'http://localhost:5000'
    for _ in range(120):
        try:
            with urllib.request.urlopen(address, timeout=1) as response:
                if response.status == 200 and b'Shorts Studio' in response.read(10000):
                    webbrowser.open(address)
                    return
        except (OSError, urllib.error.URLError):
            pass
        time.sleep(1)
    print('Browser did not open. Check the server messages, then open ' + address)


if __name__ == '__main__':
    main()
