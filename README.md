# GPT-API
## Getting Started
### Installation
***Make sure first of using a virtual enviroment.*** <br/>

You can install all necessary dependencies directly from [requirements.txt](./requirements.txt):
```bash
pip install -r requirements.txt
```

---

## Run in Development mode
There are different ways to run the server for development
### Run powershell automated script
Note: **Windows Only** for the moment. <br><br>
You can use the automated powershell script I wrote named [run.ps1](run.ps1) which will follow these steps:
- Run .venv (virtual env) and in case it doesn't exist will be created, then will install [requirements.txt](/requirements.txt) if existing.
- Run [main.py](/main.py) if existing.
```bash
# Run this command in your terminal
run.ps1
```
### Run manually
```bash
python main.py
```
If you want to enable debug mode this way, go to the [main.py](main.py) and send the debug variable as an argument:
```python
...
if __name__ == '__main__':
    app.run(debug=True)
...
```
As well, you can create a [.flaskenv](/.flaskenv) file in root path and write the env variables there, for example:
```python
# .flaskenv
FLASK_APP=main.py
FLASK_ENV=development
FLASK_DEBUG=True
```

### Run Flask manually
1. Set Flask configs
```bash
# Windows
set FLASK_APP=main.py
# In case didn't work, try this:
$env:FLASK_APP="main.py"

# Linux/MacOS
export FLASK_APP=main.py
```

2. Run server
```bash
flask run
```

---

# Production Deployment
- [Docker Deployment](#docker-deployment)
- [Manual Deployment](#manual-deployment)

## Docker Deployment
Make sure to have installed docker and docker compose in your linux instance.

1. Clone/copy project.
2. Create [.env](./.env) file as [.env.example](./.env.example)
3. Create [db/](./db/) directory and copy VectorDB as [faiss_default/](./db/faiss_default/)  inside of it.
4. Update Swagger docs [openapi.yml](./static/openapi.yaml) server ip:
    ```yaml
    # Before
    ...
    servers:
    - url: http://localhost:8000/api/v1/conversation-summary
    ...

    # Update to server:port / domain
    # Example ip:port
    servers:
    - url: http://18.220.234.246:8000/api/v1/conversation-summary
    ...
    # or
    servers:
    - url: http://domain.com/api/v1/conversation-summary
    ...
    ```
5. Run `docker-compose up` to make it run. <br>
6. If you make changes in sourcecode `docker-compose up --build` to update changes. <br>

**Note:** Containers are mean to be auto initiated when docker starts. So make sure to start docker service in your linux instance if you want to.

## Manual Deployment

When you’re developing locally, you’re using the built-in development server, debugger, and reloader.
These should not be used in production. Instead, you should use a dedicated WSGI server or hosting platform <br>
**Do not use the development server when deploying to production. It is intended for use only during local development. It is not designed to be particularly secure, stable, or efficient.**

[Flask docs: Deploying to Production](https://flask.palletsprojects.com/en/3.0.x/deploying/)


#### Instructions
Let's you're deploying over a new linux machine, once you copied project files: <br>
1. Update apt packages`sudo apt-get update` <br>
2. Install Python
    - `sudo apt install python3-pip`
    - `sudo apt install python3.11-venv`
3. Create virtual env
    - `python3.11 -m venv .venv`
4. Activate virtual env
    - `source .venv/bin/activate`
5. Install requirements
    - `pip3 install -r requirements.txt` <br>
    if pywin32 gives problem, remove it.
6. Create .env file and write your OpenAI API key
    - ```python
        # .env
        OPENAI_API_KEY=
        ```
6. Make sure to set port in main.py app init
    - ```python
        # main.py
        ...
        if __name__ == '__main__':
            app.run(host='0.0.0.0', port=8000)
        ...
        ```
7. Install gunicorn
    - `pip3 install gunicorn`
8. Run the API with gunicorn
    - Test gunicorn `gunicorn main:app`
    - Test binding port `gunicorn -b 0.0.0.0:8000 main:app &`
    - Finally `gunicorn -w 4 -b 0.0.0.0:8000 main:app &` <br>
If you ask what all that flags and arguments means, go to the [Explanation](#explanation-of-gunicorn-flags-and-arguments)

**Stop/Kill gunicorn port process:** `sudo fuser -k 8000/tcp`

#### Once your gunicorn server is working, you must make a little change in order to make Swagger docs work.
Go to the [openapi.yml](./static/openapi.yaml) file which contains all configurations for the Swagger page and change the "**url**" key from  "**servers**" key to you actual PublicIP from your machine, for example:
```yaml
...
servers:
  - url: http://3.17.174.171:8000/api/v1/conversation-summary
...
```
You should put real public ip, writing _localhost_ or _0.0.0.0_ won't work.

You may need to restart the server.

### Explanation of gunicorn flags and arguments
`gunicorn <4 workers> <bind to port> <module>:<app_name>` <br>
`gunicorn -w 4 -b 0.0.0.0:8000 main:app &` <br>

`-w 4`: **In case hundreds of calls are requested.** Specifies the number of workers to run. In this case, 4 workers are being used. Workers are individual processes that handle incoming HTTP requests concurrently. Increasing the number of workers can improve the performance of the application in high-load environments. <br>
`-b 0.0.0.0:8000`: Specifies the IP address and port that Gunicorn will listen on for incoming requests. In this case, 0.0.0.0 means Gunicorn will listen on all available network interfaces, and 8000 is the port number. Therefore, Gunicorn will be listening on all network interfaces on port 8000. <br>
`&`: Allows to run in the background. This means that after running this command, the terminal will be available for you to continue working, and the Gunicorn server will run in the background.

### Extended Docs:
#### Workers
The `-w` option specifies the number of processes to run; a starting value could be CPU * 2. The default is only 1 worker, which is probably not what you want for the default worker type.

#### Binding Externally
Gunicorn should not be run as root because it would cause your application code to run as root, which is not secure. However, this means it will not be possible to bind to port 80 or 443. Instead, a reverse proxy such as nginx or Apache httpd should be used in front of Gunicorn.

You can bind to all external IPs on a non-privileged port using the `-b 0.0.0.0` option. Don’t do this when using a reverse proxy setup, otherwise it will be possible to bypass the proxy.

```bash
$ gunicorn -w 4 -b 0.0.0.0 'hello:create_app()'
Listening at: http://0.0.0.0:8000 (x)
```
`0.0.0.0` is not a valid address to navigate to, you’d use a specific IP address in your browser.

---

### Extra recommendation:
#### Reverse Proxy
Build a Reverse Proxy like NGINX in front of the WSGI server, altough is not part of WSGI, it provides a lot of benefits, like managing thousands of connections, buffering request from clients and allows you to put multiple WSGI servers behind the proxy for horizontal scaling.