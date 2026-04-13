import os
import requests

downloads = {
    "qroo": [
        "https://preview.qroo.gob.mx/rppc2/wp-content/rppc2/uploads/2023/11/4.4-MANUAL-DE-TRAMITES-Y-SERVICIOS.pdf",
        "https://preview.qroo.gob.mx/rppc2/wp-content/rppc2/uploads/2023/11/4.2-MANUAL-DE-PROCEDIMIENTOS.pdf",
        "https://preview.qroo.gob.mx/rppc2/wp-content/rppc2/uploads/2023/12/4.1-MANUAL-DE-ORGANIZACIO%CC%81N.pdf",
        "https://preview.qroo.gob.mx/rppc2/wp-content/rppc2/uploads/2023/12/DECRETO-DE-CREACION-DEL-REGISTRO-PUBLICO.pdf",
        "https://preview.qroo.gob.mx/rppc2/wp-content/rppc2/uploads/2023/11/REGLAMENTO-RPPC-QROO.pdf"
    ],
    "puebla": [
        "https://www.ordenjuridico.gob.mx/Documentos/Estatal/Puebla/wo96788.pdf",
        "https://ojp.puebla.gob.mx/media/k2/attachments/Reglamento_de_la_Ley_del_Registro_Publico_de_la_Propiedad_del_Estado_de_Puebla_T3_06052016.pdf"
    ]
}

base_dir = "/home/ia/consulta-rpp/scratch/temp_downloads"

for state, urls in downloads.items():
    state_dir = os.path.join(base_dir, state)
    os.makedirs(state_dir, exist_ok=True)
    for url in urls:
        filename = url.split("/")[-1].replace("%CC%81", "A") # Fix encoding in filename
        filepath = os.path.join(state_dir, filename)
        print(f"Downloading {url} to {filepath}...")
        try:
            response = requests.get(url, timeout=30, verify=False) # verify=False because sometimes these govt sites have bad certs
            if response.status_code == 200:
                with open(filepath, "wb") as f:
                    f.write(response.content)
                print(f"  Success.")
            else:
                print(f"  Failed with status code: {response.status_code}")
        except Exception as e:
            print(f"  Error: {str(e)}")
