def main():
    print("Starting MITM Dump")

if __name__ == "__main__":
    import sys
    from mitmproxy.tools.main import mitmdump
    sys.argv = ['mitmdump', '--mode', 'transparent', '--showhost', '-s', 'blocklist.py','--set','block_global=false', '--ignore-hosts', 'google.com:443']
    mitmdump()
