import re
import sys

def parse_notaries(filepath, state_name):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to capture notary entries
    # The pattern seems to be: Number + " NOT. " + Name + " NOTARÍA " + Number + ", " + City
    # Then Address and Phone
    
    # Let's try to split by the pattern "[Number] NOT. "
    entries = re.split(r'(\d+ NOT\.)', content)
    
    notaries = []
    # entries[0] is everything before the first match
    for i in range(1, len(entries), 2):
        header = entries[i] # e.g. "7 NOT."
        body = entries[i+1] # the rest of the entry until the next "NOT."
        
        # Extract Name
        name_match = re.search(r'^\s*([A-ZÁÉÍÓÚÑ ]+)\s+NOTARÍA', body)
        if not name_match:
            continue
        name = name_match.group(1).strip()
        
        # Extract Notary Number
        notary_num_match = re.search(r'NOTARÍA\s*(\d+)', body)
        notary_num = notary_num_match.group(1) if notary_num_match else header.split()[0]
        
        # Extract City
        city_match = re.search(r'NOTARÍA\s*\d+,\s*([^,]+),', body)
        city = city_match.group(1).strip() if city_match else ""
        
        # Extract Address (from "CARACTER: TITULAR" or similar until state name)
        address_match = re.search(r'CARACTER:\s*\w+\s*(.+?)\s*' + re.escape(state_name), body, re.IGNORECASE | re.DOTALL)
        address = address_match.group(1).strip().replace('\n', ' ') if address_match else "No disponible"
        
        # Extract Phone (usually after "Socio desde: YYYY")
        phone_match = re.search(r'Socio desde:\s*\d{4}\s*(\d[\d\s\-\(\)]+)', body)
        phone = phone_match.group(1).strip().replace('\n', ' ') if phone_match else "No disponible"
        
        notaries.append({
            "name": name,
            "number": notary_num,
            "city": city,
            "address": address,
            "phone": phone
        })
    
    return notaries

def format_markdown(notaries, title):
    md = f"## {title}\n\n"
    md += "| No. | Titular | Ciudad | Dirección | Teléfono |\n"
    md += "|---|---|---|---|---|\n"
    for n in notaries:
        md += f"| {n['number']} | {n['name']} | {n['city']} | {n['address']} | {n['phone']} |\n"
    return md

if __name__ == "__main__":
    puebla_file = "/home/ia/.gemini/antigravity/brain/3d3ebbd8-089a-4feb-9b72-f5ee4bc96c30/.system_generated/steps/76/content.md"
    qroo_file = "/home/ia/.gemini/antigravity/brain/3d3ebbd8-089a-4feb-9b72-f5ee4bc96c30/.system_generated/steps/85/content.md"
    
    puebla_notaries = parse_notaries(puebla_file, "PUEBLA")
    qroo_notaries = parse_notaries(qroo_file, "QUINTANA ROO")
    
    with open("/home/ia/consulta-rpp/docs/rpp_expert/DIRECTORIO_NOTARIOS_FULL_2026.md", "w") as out:
        out.write("# DIRECTORIO COMPLETO DE NOTARIOS PÚBLICOS (2026)\n\n")
        out.write(format_markdown(puebla_notaries, "ESTADO DE PUEBLA"))
        out.write("\n\n")
        out.write(format_markdown(qroo_notaries, "ESTADO DE QUINTANA ROO"))
    
    print(f"Parsed {len(puebla_notaries)} notaries for Puebla and {len(qroo_notaries)} for Quintana Roo.")
