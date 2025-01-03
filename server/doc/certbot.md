# How to create an SSL certificate?

1. Install certbot in WSL

```shell
sudo snap install --classic certbot
```

2. Link certbot files

```shell
sudo ln -s /snap/bin/certbot /usr/bin/certbot
```

3. Run certbot manual command and enter the domains

```shell
sudo certbot certonly --manual --preferred-challenges=http
```

5. Create challenge endpoint(s)

```python
@app.get('/.well-known/acme-challenge/<Key>')
async def certbot_challenge(_):
    return '<Value>'
```

6. Restart the microcontroller app
7. Manually test the endpoints
8. Click ENTER in the certbot window to continue with the validation
9. Voila, you have now generated free SSL certificates at:

`/etc/letsencrypt/live/<domain>/fullchain.pem`

and

`/etc/letsencrypt/live/<domain>/privkey.pem`

6. Copy and convert the files to .der format

```shell
openssl x509 -outform der -in fullchain.pem -out cert.der
```

```shell
openssl ec -outform der -in privkey.pem -out key.der
```

7. Manually renew the certificates by following the same procedure again (starting with step 3)