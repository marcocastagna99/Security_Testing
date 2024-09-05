container da testare per il mio scan

controllare sempre ip del container, e eliminare il target id ogni volta se ripeto la scanansione, vedere targets.py


docker run --rm -it -p 8080:80 vulnerables/web-dvwa
docker run --rm -p 3000:3000 bkimminich/juice-shop

openVas con gvm per utilizzare API REST
docker run -d -p 443:443 -p 9390:9390 -p 80:80 --name openvas securecompliance/gvm:11.0.1-r3



Running on http://127.0.0.1:5000
Running on http://172.30.56.250:5000

esempio di input da curl
curl -X POST http://localhost:5000/trigger_scan -H "Content-Type: application/json" -d '{
  "scan_name": "DVWA Scan",
  "targets": ["172.17.0.3"]
}'

curl -X POST \
  http://172.17.0.1:5000/trigger_scan \
  -H 'Content-Type: application/json' \
  -d '{
    "scan_name": "MyScan",
    "targets": ["172.17.0.3"]
  }'

recupero i resultati
Sostituisci mock_task_id con l'ID del task reale che ottieni dalla risposta del primo comando
curl -X GET http://localhost:5000/scan_status/<task_id>




curl -X POST http://localhost:5000/trigger_scan -H "Content-Type: application/json" -d '{
  "scan_name": "DVWA Scan",
  "targets": ["172.17.0.4"]
}'


aggiustare get task result !




