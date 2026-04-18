Hosting
=======

While this application permits the hosting of multiple documents through one website it is often convenient to merely host the documentation for one project.
This can be done with the following script:

.. code-block:: python
    :caption: docs/__main__.py
    :linenos:

    import http.server
    import socketserver
    import functools

    HOST = ""
    PORT = 8000
    DOCS = ".build/html"
        
    Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=DOCS)

    with socketserver.TCPServer((HOST, PORT), Handler) as httpd:
        print(f"Serving {DOCS} through port {PORT}")
        httpd.serve_forever()

or merely through the command `python -m http.server [port] --directory [directory]` e.g. `python -m http.server 8000 -- directory docs/.build/html`.