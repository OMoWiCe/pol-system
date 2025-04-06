# pol-system
Programs running inside the Point of Location (POL) device


# Steps
### 1. Clone the repository

```bash
git clone https://github.com/OMoWiCe/pol-system.git pol-system
```

### 2. Create a virtual environment
Setup a virtual environment inside the `pol-system` directory.
```bash
cd pol-system
python3 -m venv venv
```

### 3. Install the required packages
```bash
source venv/bin/activate
pip install azure-iot-device && pip install numpy && pip install dotenv
deactivate
```

### 3. Configure the system properties
- The configuration file is located at `pol-system/system.properties` file.
- Envronment variables are defined in the `pol-system/.env` file. Add `IOT_HUB_CONNECTION_STRING` and `OBFUSCATE_SECRET` to the `.env` file.

### 4. Update file permissions
```bash
chmod +x main-program.py
```

### 5. Run the system
```bash
./main-program.py
```
 

