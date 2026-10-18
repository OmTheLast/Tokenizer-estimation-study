"""Create original, public, templated fixtures without tokenizing them."""
import ast, hashlib, html, json, pprint
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MESSAGES=[
 ['Check the water level.','पानी का स्तर जाँचें।','நீரின் அளவைச் சரிபார்க்கவும்.'],
 ['Close the window before leaving.','जाने से पहले खिड़की बंद करें।','செல்வதற்கு முன் சன்னலை மூடவும்.'],
 ['Put the books on the shelf.','किताबें शेल्फ पर रखें।','புத்தகங்களை அலமாரியில் வைக்கவும்.'],
 ['Count the red boxes.','लाल डिब्बों को गिनें।','சிவப்பு பெட்டிகளை எண்ணவும்.'],
 ['Save the latest report.','नवीनतम रिपोर्ट सहेजें।','சமீபத்திய அறிக்கையைச் சேமிக்கவும்.'],
 ['Send the meeting notes.','बैठक के नोट्स भेजें।','கூட்டக் குறிப்புகளை அனுப்பவும்.'],
 ['Measure the length of the table.','मेज़ की लंबाई मापें।','மேசையின் நீளத்தை அளக்கவும்.'],
 ['Turn off the lights.','बत्तियाँ बंद करें।','விளக்குகளை அணைக்கவும்.'],
 ['Update the delivery address.','डिलीवरी का पता अपडेट करें।','விநியோக முகவரியைப் புதுப்பிக்கவும்.'],
 ['Find the missing key.','गुम हुई चाबी ढूँढें।','காணாமல் போன சாவியைக் கண்டுபிடிக்கவும்.'],
 ['Clean the small container.','छोटे बर्तन को साफ़ करें।','சிறிய பாத்திரத்தைச் சுத்தம் செய்யவும்.'],
 ['Record the room temperature.','कमरे का तापमान दर्ज करें।','அறையின் வெப்பநிலையைப் பதிவு செய்யவும்.']]
FORMATS=['prose','python','json_compact','json_pretty','html']
CONDITIONS=['english','english_hindi','english_tamil']
class TableReader(HTMLParser):
    def __init__(self): super().__init__(convert_charrefs=True);self.attrs={};self.cells=[];self.incell=False
    def handle_starttag(self,tag,attrs):
        if tag=='table':self.attrs=dict(attrs)
        if tag=='td':self.incell=True;self.cells.append('')
    def handle_endtag(self,tag):
        if tag=='td':self.incell=False
    def handle_data(self,data):
        if self.incell:self.cells[-1]+=data

def render(record,kind):
    if kind=='json_compact':return json.dumps(record,ensure_ascii=False,separators=(',',':'))
    if kind=='json_pretty':return json.dumps(record,ensure_ascii=False,indent=2)
    if kind=='python':return 'record = '+pprint.pformat(record,sort_dicts=False,width=88)+'\n'
    if kind=='prose':
        text=f"Batch {record['batch']}. Active: {str(record['active']).lower()}.\n"
        return text+'\n'.join(f"Item {item['id']}; quantity {item['quantity']}; message: {item['message']}" for item in record['items'])
    if kind=='html':
        lines=[f'<table data-batch="{record["batch"]}" data-active="{str(record["active"]).lower()}">','  <thead><tr><th>ID</th><th>Quantity</th><th>Message</th></tr></thead>','  <tbody>']
        lines.extend(f'    <tr><td>{item["id"]}</td><td>{item["quantity"]}</td><td>{html.escape(item["message"])}</td></tr>' for item in record['items'])
        return '\n'.join(lines+['  </tbody>','</table>'])
    raise ValueError(kind)

def validate_render(text,kind,record):
    if kind.startswith('json_'):assert json.loads(text)==record
    elif kind=='python':
        module=ast.parse(text);assert len(module.body)==1 and isinstance(module.body[0],ast.Assign)
        assert ast.literal_eval(module.body[0].value)==record
    elif kind=='html':
        p=TableReader();p.feed(text);assert p.attrs=={'data-batch':record['batch'],'data-active':str(record['active']).lower()}
        assert p.cells==[str(v) for item in record['items'] for v in [item['id'],item['quantity'],item['message']]]
    else:
        assert record['batch'] in text and all(item['message'] in text for item in record['items'])

def build():
    rows=[];records=[]
    for i in range(12):
        n=[1,3,6][i//4]
        for ci,condition in enumerate(CONDITIONS):
            record={'batch':f'batch-{i+1:02d}','active':i%2==0,'items':[{'id':100*(i+1)+j,'quantity':1+(i+j)%9,'message':MESSAGES[(i+j)%12][ci]} for j in range(n)]}
            records.append({'scenario':f's{i+1:02d}','condition':condition,'item_count':n,'record':record})
            for kind in FORMATS:
                text=render(record,kind);validate_render(text,kind,record)
                rows.append({'id':f's{i+1:02d}/{condition}/{kind}','scenario':f's{i+1:02d}','condition':condition,'format':kind,'item_count':n,'role':'primary','text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest()})
    probes=[('ascii','A = 1\nB = 2\n'),('whitespace','A  =  1\n\tB = 2\n\n'),('composed','café naïve'),('decomposed','cafe\u0301 nai\u0308ve'),('emoji','Status: ready ✅ 🧪 🚀.'),('rare_characters','Symbols: 𠮷 𓀀.'),('indentation','def ready():\n    return True\n'),('literal_space_marker','Marker: ▁ and tab:\tend.')]
    for name,text in probes:rows.append({'id':'probe/'+name,'scenario':name,'condition':'probe','format':'probe','item_count':None,'role':'probe','text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest()})
    assert len(rows)==188 and len({r['id'] for r in rows})==188
    assert len({r['text_sha256'] for r in rows})==188
    return {'name':'text-types-v1','authorship':'Original Codex-authored illustrative fixtures; not scraped, not FLORES; translations not independently validated.','sampling':'12 templated scenario blocks × 3 content conditions × 5 renderers, plus 8 separate diagnostic probes. Not natural traffic.','conditions':CONDITIONS,'formats':FORMATS,'records':records,'inputs':rows}
if __name__=='__main__':
    out=ROOT/'data/fixtures/text-types-v1.json';out.parent.mkdir(parents=True,exist_ok=True)
    data=json.dumps(build(),ensure_ascii=False,indent=2)+'\n'
    if out.exists():assert out.read_text()==data,'Frozen corpus differs; create a new version instead.'
    else:out.write_text(data)
    print('Created/verified 180 primary inputs and 8 diagnostic probes; render checks passed. No encoding performed.')
