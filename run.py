import index

app = index.app

if __name__ == '__main__':
    app.run_server(debug=True,
    #dev_tools_ui=False ##Uncomment to demo app without errors popping up
    )