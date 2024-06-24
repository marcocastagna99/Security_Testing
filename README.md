container da testare per il mio scan

docker run --rm -it -p 80:80 vulnerables/web-dvwa
docker run --rm -p 3000:3000 bkimminich/juice-shop

curl -X POST http://localhost:5000/trigger_scan -H "Content-Type: application/json" -d '{
  "scan_name": "DVWA Scan",
  "targets": ["192.168.1.100"]
}'

recupero i resultati
Sostituisci mock_task_id con l'ID del task reale che ottieni dalla risposta del primo comando
curl -X GET http://localhost:5000/get_report/mock_task_id
