container da testare per il mio scan

docker run --rm -it -p 80:80 vulnerables/web-dvwa
docker run --rm -p 3000:3000 bkimminich/juice-shop
docker run -d -p 443:443 -p 9390:9390 -p 80:80 --name openvas securecompliance/gvm:11.0.1-r3

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


aggiustare get task result



capire il discorso della tabellla scans se la crea o meno