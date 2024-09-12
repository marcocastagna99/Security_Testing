container da testare per il mio scan

controllare sempre ip del container, e eliminare il target id ogni volta se ripeto la scanansione, vedere targets.py

container vulnerabili
docker run --rm -it -p 8080:80 vulnerables/web-dvwa
docker run --rm -it -p 8081:8080 webgoat/webgoat-8.0
docker run --rm -it -p 22:22 -p 8090:80 -p 3307:3306 tleemcjr/metasploitable2
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

curl -X POST http://127.0.0.1:5000/trigger_scan -H "Content-Type: application/json" -d '{
  "scan_name": "DVWA Scan",
  "targets": ["172.17.0.3"]
}'

recupero i resultati
Sostituisci mock_task_id con l'ID del task reale che ottieni dalla risposta del primo comando
curl -X GET http://localhost:5000/scan_status/scan_name?task_id=taskid1

esempio  (%20 per lo spazio)

curl -X GET "http://localhost:5000/scan_status/DVWA%20Scan?task_id=498b6fe9-6f54-41
f6-ace7-2e5585f24c11"

se 2 task 
curl -X GET "http://localhost:5000/scan_status/My_Scan?task_id=task_id1&task_id=task_id2"


vedere i targets

curl -X GET http://localhost:5000/openvas_targets


eliminare i targets
curl -X POST http://localhost:5000/delete_targets \
-H "Content-Type: application/json" \
-d '{"target_ids": ["12345", "67890", "112233"]}'

esempio: 
curl -X POST http://localhost:5000/delete_targets \
-H "Content-Type: application/json" \
-d '{"target_ids": ["733f243c-cac4-42c5-8cdb-857c7b9e50d2", "136820aa-c2a7-47fd-ba99-33478af055b5"]}'


vedere gli scanner disponibili su openVas:

curl -X GET http://localhost:5000/scanners






curl -X POST http://localhost:5000/trigger_scan -H "Content-Type: application/json" -d '{
  "scan_name": "My_Scan",
  "targets": ["172.17.0.3", "172.17.0.4"]
}'


aggiustare get task result !


FORSE CON IL REPORT SI RIESCE MEGLIO

TO DO (alla fine)
scan_list (lista degli scanner)
delete_target
targets 
come funzioni della libreria invece di file a parte, dare la possibilità tramite rest service di utilizzarli   (non richiesto)




funziona su un target, vedere come far funzionare su due target, capire il discorso dei thread che moitorano  (fatto)