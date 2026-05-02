# Static Webserver

## Introduction

This is the webserver made for hosting static content. 
It has request logging and can be extended with various admin pages.

## Infrastucture

### Server
This is tested on an AWS lightsail instance but should work on any similar linux server.
The keypair for SSH access to the instance should be stored as ServerKey.pem
After making the lightsail instance, assign it a static IP. 

### pip3
Make sure pip3 is installed on the server so python3 can import modules
```
sudo yum update -y
sudo yum install python3-pip -y
```

### Nginx
In order to serve the webserver on the right port, Nginx is used
To install Nginx on the lightsail instance:
```
sudo yum install nginx -y
```
Then start it and enable it on boot
```
sudo systemctl start nginx
sudo systemctl enable nginx
```
Next open the configuration
```
sudo nano /etc/nginx/nginx.conf
```
Replace the server block inside the http block
```
# Example snippet inside the http block of nginx.conf (replace error stubs)
    server {
        listen 80;
        server_name LIGHTSAIL_DOMAIN_OR_PUBLIC_IP;

        location / {
            # Pass all requests coming to port 80 to the Python server on 1500
            proxy_pass http://127.0.0.1:1500;

            # Headers for proxying
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Increase buffer size
            proxy_buffer_size 128k;
            proxy_buffers 4 256k;
            proxy_busy_buffers_size 256k;
        }
    }
```
Finally, test the new configuration and restart Nginx
```
sudo nginx -t
sudo systemctl restart nginx
```

### HTTPS
The above steps will allow the server to be accessed at the static IP on port 80 (HTTP)
To enable port 443 (HTTPS) a few more steps are needed
1. Enable port 443 in the IPv4 firewall for the lightsail instance
2. Must have a domain name associated with the instance
3. Install Certbot
```
sudo yum install certbot python3-certbot-nginx -y
```
4. Edit the Nginx config again and change server_name to be the domain instead of the IP (if needed)
```
sudo nano /etc/nginx/nginx.conf
sudo nginx -t
sudo systemctl reload nginx
```
5. Run certbot to generate the https cert
```
sudo certbot --nginx -d DOMAIN
sudo systemctl reload nginx
```
HTTPS should now be live! Certbot will autorenew the cert every 90 days

## Deployment
Install python modules in .venv
```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```
Use the deploy.py script to deploy the server both locally (for testing) and remotely
```
./deploy.py local
./deploy.py server
```
Additionally, use the deploy.py script to deploy the site itself from a zip file separately
```
./deploy.py local-site <zip_file>
./deploy.py server-site <zip_file>
```
Note: this will replace the entire contents of ~/site/ on the server (or site/ locally) with the zip file contents

## Monitoring & Cleanup
To stop the server, use CTRL-C locally or the following commands for remote. The second command must be run on the server, but both do the same thing.
```
./deploy.py kill
sudo systemctl stop pyserver
```
On the remote server, use the following command to check server status
```
systemctl status pyserver
```

## Managing Logs

Logs are rotated based on the LOG_NUMBER and LOG_SIZE variables. A LOG_NUMBER of 3 and LOG_SIZE of 1024 will result in 4 log files (3 + active file) 1KB each at maximum for a total possible size of 4KB.

Log rotation appends a number that indicates age. The requests.log file is always the latest logs as it is the file that gets written to. The requests.log.1 file is the last full requests log, requests.log.2 is the previous and so on. Every time the requests.log file gets full these are renamed to increment their number, deleting the oldest if LOG_NUMBER is exceeded.

When downloading logs it is recommended to rename the files in the following way: 
1. Any log file with a number appended to it should have the number replaced with the timestamp from the first log inside it.
2. If the current .log file is downloaded it should be renamed to have both the timestamp and the word PARTIAL in it so that it is replaced on a subsequent download.

The following command can be used on linux systems to extract the first timestamp from a log file.
```
head -c 21 requests.log
```
For most cases, a naming system that only uses the date component of the timestamp is optimal.
