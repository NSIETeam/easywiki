import sys

with open(r'C:\Users\T14\AppData\Local\Temp\webview_test.log', 'w') as f:
    f.write('START\n')
    f.flush()
    try:
        import webview
        f.write('webview imported\n')
        f.flush()
        webview.create_window('test', 'https://example.com')
        f.write('window created\n')
        f.flush()

        import threading
        import time

        def stop_after():
            time.sleep(3)
            f.write('timer fired\n')
            f.flush()
            for w in webview.windows:
                w.destroy()

        threading.Thread(target=stop_after, daemon=True).start()
        webview.start()
        f.write('start returned\n')
        f.flush()
    except Exception as e:
        import traceback
        f.write('ERROR: ' + str(e) + '\n')
        f.write(traceback.format_exc())
        f.flush()
