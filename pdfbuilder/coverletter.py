def default_coverletter_function(coverletter, request, config):
    return """
<html><head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
</head><body>%s</body></html>""" % coverletter
