1.	Dataset Download 
		curl -L "https://app.roboflow.com/ds/LlLwwZUHid?key=0DI584HVfr" > roboflow.zip; unzip roboflow.zip; rm roboflow.zip

2.	Libraries needed
	Torch, Ultralytics , wandb --- hopefully everything else will be installed as requirements for torch and ultralytics

3. 	Data setup
	results = model.train(data="/path/to/data.yaml(from dataset download)"

4.	Debugging tips
	1.	images not found  - open data.yaml and set correct paths to the datasets
