from fasthtml.common import FastHTML, Form, Input, Button, serve  

app = FastHTML()

@app.route("/")
def get() :
    return Form(
Input(type="text"),
Input(type="textarea", placeholder="Enter text here"),
Button("Sumbit")


    )


serve()