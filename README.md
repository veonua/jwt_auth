[![](https://images.microbadger.com/badges/version/veonua/jwt_auth.svg)](https://microbadger.com/images/veonua/jwt_auth)

# JWT Authentication for K8s ingress

Simple external authentication microservice for a Nginx. 
Implements JWT with RS256 algorithm 

This application uses PyJwt to validate signature https://pyjwt.readthedocs.io/en/latest/

This code was created for use with the [NGINX Ingress Controller](https://github.com/nginxinc/kubernetes-ingress)
and [Kubernates Ingress Controller](https://github.com/kubernetes/ingress-nginx)
not tested with other controllers.

>TODO: Helm chart

Http server expects auth token in the "Authorization: Bearer {JWT}" header
service decodes claims and sends extended headers in format

`X-JWT-{claim-key}: {claim-value}`

so these claims are accessable via  `auth_request_set $jwt_claim_name1 $upstream_http_x_jwt_name1;` in Nginx configuration file
            

Example of JWT-claim based routing in the Nginx-Ingress

``` yaml
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  annotations:
    certmanager.k8s.io/cluster-issuer: letsencrypt-production
    kubernetes.io/ingress.class: nginx
    nginx.org/server-snippets: |
        resolver 10.0.0.10 ipv6=off;

        location = /_auth {
            internal;
            proxy_pass http://jwt.default.svc.cluster.local:8000;
            proxy_pass_request_body off;
            proxy_set_header  Content-Length "";
            proxy_set_header  X-Original-URI $request_uri;
        } 

        location ~ /(.*) {
            proxy_buffering off;
            proxy_connect_timeout 360s;
            proxy_read_timeout 360s;
            proxy_send_timeout 360s;
            client_max_body_size 10m;
            #proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-Server $host;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            
            auth_request /_auth;
            auth_request_set $jwt_claim_tenant $upstream_http_x_jwt_tenant;
            proxy_pass "http://$jwt_claim_tenant-$1.default.svc.cluster.local:8080/";
            }
  name: example
  
spec:
  rules:
  - host: domain.example.com
    http:
      paths:
      - backend:
          serviceName: unsecure
          servicePort: 8000
        path: /unsecure
  tls:
  - hosts:
    - domain.example.com
    secretName: tls-secret

```