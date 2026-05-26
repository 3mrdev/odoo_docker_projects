
import json
import base64
import datetime

from ast import literal_eval
from collections import defaultdict
from odoo.http import request
from odoo.exceptions import AccessError, MissingError, UserError
from odoo.addons.appness_logspace_portal.models import helpers

ALLOWED_IMAGE_FORMATS = ["image/jpeg", "image/png", "image/tiff"]

def _prepare_files(params,params_to_pop,partner_id):
    internal_folder = request.env.ref('documents.document_internal_folder').id
    document_type = request.env['logspace.document.type'].sudo()
    m2o_params = {}
    o2m_params = {}
    binary_params = {}

    IrConfigSudo = request.env["ir.config_parameter"].sudo()

    max_attachment_size = IrConfigSudo.get_param("appness_logspace_portal.attachment_size_limit")
    if max_attachment_size:
        max_attachment_size = float(max_attachment_size)
        max_attachment_size_bytes = max_attachment_size * 1024 * 1024 #Convert MegaBytes to Bytes
    else:
        max_attachment_size = 2
        max_attachment_size_bytes = max_attachment_size * 1024 * 1024 #Convert MegaBytes to Bytes

    for field_name, field_value in params.items():
        
        if field_name and field_value == '“”':
            if params[field_name]:
                field_value = False
                params[field_name] = False

        if '_issuance_date' in field_name:
            params_to_pop.append(field_name)
            
        if '_expire_date' in field_name:
            params_to_pop.append(field_name)

        if '_m2o_' in field_name:
            if field_value and field_value != '“”':
                m2o_params[field_name.split('_m2o_')[0]]= int(field_value)
            params_to_pop.append(field_name)

        if '_o2m_' in field_name:
            o2m_list = request.httprequest.form.getlist(field_name)
            if o2m_list:
                o2m_params[field_name]= o2m_list
            params_to_pop.append(field_name)

        if hasattr(field_value, 'filename'):
            attached_file = field_value.read()
            if attached_file:
                file_size = len(attached_file) 
                file_size_mb = file_size / 1024 / 1024 
                
                if file_size > max_attachment_size_bytes:
                    raise UserError(f"The attachment exceed the maximum attachment size please make sure to insert attachment less than or equal to [{max_attachment_size} MB]. \nYour current file named '{field_value.filename}' has a size of [{round(file_size_mb,2)} MB] refresh the page and try again!")

                #TODO: future idea to imporve binary files upload to include all binary fields
                if 'image' in field_name:
                    if field_value.mimetype in ALLOWED_IMAGE_FORMATS:
                        binary_params[field_name] = base64.encodebytes(attached_file)
                    else:
                        #TODO: future idea to import error by saving all data and skip the files with an error in the portal
                        raise UserError(f"Only image files (JPEG, PNG, TIFF) are allowed. \n Your current file is {field_value.mimetype}")
                else:
                    if field_value.mimetype in ALLOWED_IMAGE_FORMATS or field_value.mimetype in ["application/pdf"]:
                        params_to_pop.append(field_name)
                        issuance_date = False
                        expire_date = False

                        for fn, fv in params.items():
                            if field_name + '_issuance_date' in fn:
                                issuance_date = params[fn] or False
                                # params_to_pop.append(field_name + '_issuance_date')
                            if field_name + '_expire_date' in fn:
                                expire_date = params[fn] or False
                                # params_to_pop.append(field_name + '_expire_date')

                        document_type_id = document_type.search([('code','=',field_name)],limit=1)
                        if document_type_id:
                            request.env['documents.document'].sudo().create({
                                'name': field_value.filename,
                                'mimetype':field_value.mimetype,
                                'datas': base64.encodebytes(attached_file),
                                'folder_id': internal_folder,
                                'issuance_date': issuance_date,
                                'expire_date': expire_date,
                                'doc_type': document_type_id.id,
                                'owner_id': request.env.ref('base.user_root').id,
                                'partner_id': partner_id,
                            })
                    else:
                        raise UserError(f"This type of file is not allowed {field_value.mimetype} - {field_name}!!")
            else:
                params_to_pop.append(field_name)

    return params_to_pop,m2o_params,o2m_params,binary_params

def _parse_domain(domain):
    try:
        domain = literal_eval(domain)
    except Exception:
        domain = [('id', 'in', [])]
    return domain

# Function to check if all values in a dictionary are empty
def is_empty_row(d):
    return all(value in ["",'“”'] for value in d.values())

def _insert_o2m_records_in_main(stepper_id, relation_field_id, o2m_records):
    for field_name, field_records in o2m_records.items():
        relation = ''
        relation_field = ''
        for step in stepper_id.steps_ids:
            for line in step.lines:
                if line.line_field.name == field_name:
                    relation = line.line_field.relation
                    relation_field = line.line_field.relation_field
        if relation:
            relation_model = request.env[relation].sudo()
            for rec in field_records:

                for rec_f_name, rec_f_value in rec.items():
                    if rec_f_name != "id" and rec_f_value in ["",'“”']:
                        rec[rec_f_name] = False

                if 'id' in rec:
                    rec_id = rec.pop('id')
                    if rec_id == '':
                        rec[relation_field] = relation_field_id
                        relation_model.create(rec)
                    else:
                        up_rec = relation_model.search([('id','=',int(rec_id))])
                        up_rec.write(rec)

def _prepare_o2m_records(o2m_params):
    # Dictionary to hold transformed structure
    o2m_records = defaultdict(list)

    # Iterate over the keys in p1
    for key, values in o2m_params.items():
        if "_o2m_" in key:  
            main_key, field_name = key.split("_o2m_")  # Extract dynamic parts

            # Ensure we have enough entries in the list to match others
            while len(o2m_records[main_key]) < len(values):
                o2m_records[main_key].append({})  # Initialize empty dictionaries
            
            # Assign the values to the corresponding dictionary
            for i, value in enumerate(values):
                o2m_records[main_key][i][field_name] = int(value) if value.isdigit() else value  # Dynamically insert data
    
    o2m_records = dict(o2m_records)
    
    # Filter each list, removing empty rows
    filtered_o2m_records = {
        key: [item for item in value if not is_empty_row(item)]
        for key, value in o2m_records.items()
    }

    # Convert defaultdict to normal dict
    return filtered_o2m_records

def _prepare_request_service_values(service_id):
    service = request.env["product.template"].sudo().search([
        ('is_logspace','=',True),
        ('is_published_logspace','=',True),
        ('type','=','service'),
        ('id','=',service_id),
    ],limit=1)
    if service:
        return {
            "service_id":service_id,
            "service_name":service.name,
            "service_desc":service.description_sale,
        }
    else:
        return {
            "service_id":False,
        }

def _prepare_documents_values(partner_id,logspace_request):
    required_docs_list = []
    expired_documents_list = []
    required_docs,expire,issuance,expired_documents= "","","",""
    family = False

    if logspace_request:
        vdoc = helpers.validate_documents(request,logspace_request,True)
        required_docs_list += vdoc['types_list']
        required_docs += vdoc['types']
        expire += vdoc['expire']
        issuance += vdoc['issuance']
        expired_documents_list += vdoc['expired_list']
        expired_documents += vdoc['expired']

    if partner_id:
        family = request.env['res.partner'].sudo().browse(partner_id)
        if family:
            vdoc = helpers.validate_documents(request,family)
            required_docs_list += vdoc['types_list']
            required_docs += vdoc['types']
            expire += vdoc['expire']
            issuance += vdoc['issuance']
            expired_documents_list += vdoc['expired_list']
            expired_documents += vdoc['expired']
            for member in family.child_ids:
                mdoc = helpers.validate_documents(request,member)
                required_docs_list += mdoc['types_list']
                required_docs += mdoc['types']
                expire += mdoc['expire']
                issuance += mdoc['issuance']
                expired_documents_list += mdoc['expired_list']
                expired_documents += mdoc['expired']

    family_members = []
    if family:
        family_members.append(family.id)

        if family.child_ids:
            for child in family.child_ids:
                family_members.append(child.id)
        
        documents = request.env["documents.document"].sudo().search([
            ('partner_id', 'in', family_members),
            ('is_archived','=',False), #Don't show archived documents in portal
        ])

        docs = []
        for doc in documents:
            docs.append({
                "name":doc.name,
                "doc_type_name":doc.doc_type.name,
                "doc_type_code":doc.doc_type.code,
                "issuance_date":doc.issuance_date,
                "expire_date":doc.expire_date,
                "thumbnail":doc.thumbnail,
                "is_service":False,
            })
        if docs:
            return {
                "current_documents":docs,
                "required_docs":required_docs,
                "required_docs_list":required_docs_list,
                "expired_documents_list":expired_documents_list,
                "expired_documents":expired_documents,
            }
        else:
            return {
                "current_documents":False,
                "required_docs":required_docs,
                "required_docs_list":required_docs_list,
                "expired_documents_list":expired_documents_list,
                "expired_documents":expired_documents,
            }

def _prepare_logspace_form_values(stepper,page_id,logspace_request,partner_id):        
    page_id = page_id if page_id <= len(stepper.steps_ids) else False
    is_service = False

    if logspace_request:
        is_service = True
    else:
        if partner_id:
            family = request.env['res.partner'].sudo().browse(partner_id)
    
    if stepper:
        steps = []
        count = 0
        for step in stepper.steps_ids.sorted(key=lambda l: l.sequence):
            count += 1
            fields = []
            documents = []
            for line in step.lines.sorted(key=lambda l: l.sequence):
                field_vals = get_field_logspace(line.line_field, stepper, logspace_request, partner_id, line.line_fields_v2_ids, line.line_domain)
                field_vals["required"] = line.is_mandatory
                field_vals["label"] = line.name
                field_vals["tip"] = line.tip
                field_vals["validation_type"] = line.validation_type
                fields.append(field_vals)
                
            for type in step.document_types_ids:
                today = datetime.date.today()
                max_issuance_days = datetime.timedelta(days=type.max_issuance_date)
                max_expire_days = datetime.timedelta(days=type.max_expire_date)
                max_issuance_date = today - max_issuance_days
                max_expire_date = today + max_expire_days

                documents.append({
                    "label":type.name or '',
                    "name":type.code or '',
                    "description":type.description or '',
                    "is_service":is_service,
                    "is_mandatory":type.is_mandatory,
                    "issuance_date_is_mandatory":type.issuance_date_is_mandatory,
                    "expire_date_is_mandatory":type.expire_date_is_mandatory,
                    "issuance_date_is_visible":type.issuance_date_is_visible,
                    "expire_date_is_visible":type.expire_date_is_visible,
                    "max_issuance_date":max_issuance_date,
                    "max_expire_date":max_expire_date,
                    "expire_date":False,
                    "issuance_date":False,
                    "tip":"TIP", #TODO: add dynamic tip
                    "disabled":False,
                })
            
            steps.append({
                "sequence":step.sequence,
                "page_id":count,
                "name":step.name,
                "icon":step.icon,
                "fields":fields,
                "documents":documents
            })

        return {
            "stepper":stepper.name,
            "description":stepper.description,
            "steps":steps,
            "page_id":page_id,
            'error': {},
            'error_message': [],
        }
    else:
        return {
            "stepper":False,
            "steps":[],
            "page_id":page_id,
            'error': {},
            'error_message': [],
        }

def get_field_logspace(field,stepper,logspace_request,partner_id,line_fields_ids=[],field_domain=[]):
    x2m_fields = []
    disabled = False
    
    ftype = "text"
    value = ''
    options = []
    if field.ttype in ["char","json","properties"]:
        ftype = "text"
    elif field.ttype in ["text","html"]:
        ftype = "textarea"
    elif field.ttype in ["date"]:
        ftype = "date"
    elif field.ttype in ["datetime"]:
        ftype = "datetime-local"
    elif field.ttype in ["integer","float","monetary"]:
        ftype = "number"
    elif field.ttype in ["selection"]:
        ftype = "select"
        for option in field.selection_ids:
            options.append({
                "name":option.name,
                "value":option.value,
            })
    elif field.ttype in ["many2one","many2one_reference","reference"]:
        ftype = "many2one"
        # domain = json.loads(field.domain) if field.domain else []
        domain = []
        if field_domain:
            domain = _parse_domain(field_domain)
        foptions = request.env[field.relation].sudo().search(domain)
        for option in foptions:
            options.append({
                "name":option.display_name,
                "value":option.id,
            })

        if logspace_request:
            if field.model_id.model == stepper.stepper_model_id.model:
                if logspace_request[field.name]:
                    value = logspace_request[field.name].id
                    if logspace_request.stage_id.id in logspace_request.team_id.stages_allowed_to_edit_portal.ids:
                        disabled = False
                    else:
                        disabled = True
        else:
            if stepper.stepper_model_id.model == 'res.partner':
                if partner_id:
                    family = request.env['res.partner'].sudo().browse(partner_id)
                    if family:
                        if field.model_id.model == stepper.stepper_model_id.model:
                            if family[field.name]:
                                value = family[field.name].id
                                if family.allow_editing_portal:
                                    disabled = False
                                else:
                                    disabled = True

    elif field.ttype in ["many2many"]:
        ftype = "many2many"
        domain = json.loads(field.domain) if field.domain else []
        foptions = request.env[field.relation].sudo().search(domain,limit=10)
        for option in foptions:
            options.append({
                "name":option.display_name,
                "value":option.id,
            })
    elif field.ttype in ["one2many"]:
        ftype = "one2many"
        domain = json.loads(field.domain) if field.domain else []
        foptions = request.env[field.relation].sudo().search(domain,limit=10)
        for option in foptions:
            options.append({
                "name":option.display_name,
                "value":option.id,
            })
        
        #TODO: sub field domain filters
        for sub_field in line_fields_ids.sorted(key=lambda l: l.sequence):
            field_vals = get_field_logspace(sub_field.v2line_field,stepper,logspace_request,partner_id,[],sub_field.v2line_domain)
            field_vals["required"] = sub_field.is_mandatory
            field_vals["label"] = sub_field.name
            x2m_fields.append(field_vals)

        records = []
        if logspace_request:
            if logspace_request[field.name]:
                for rec in logspace_request[field.name]:
                    sub_filed_val = {
                        "id":rec.id,
                        "disabled":True
                    }
                    
                    if logspace_request.stage_id.id in logspace_request.team_id.stages_allowed_to_edit_portal.ids:
                        sub_filed_val["disabled"] = False
                    else:
                        sub_filed_val["disabled"] = True

                    for sub_field in line_fields_ids.sorted(key=lambda l: l.sequence):
                        if sub_field.v2line_field.ttype in ["many2one"]:
                            sub_filed_val[sub_field.v2line_field.name] = rec[sub_field.v2line_field.name].id
                        else:
                            sub_filed_val[sub_field.v2line_field.name] = rec[sub_field.v2line_field.name]
                    records.append(sub_filed_val)
                value = records

        if stepper.stepper_model_id.model == 'res.partner':
            if partner_id:
                family = request.env['res.partner'].sudo().browse(partner_id)
                if family:
                    if family[field.name]:
                        for rec in family[field.name]:
                            is_edit = False
                            if field.relation == 'res.partner':
                                is_edit = True
                            sub_filed_val = {
                                "id":rec.id,
                                'is_edit':is_edit,
                                'is_delete':True,
                                "disabled":True
                            }

                            if family.allow_editing_portal:
                                sub_filed_val["disabled"] = False
                            else:
                                sub_filed_val["disabled"] = True

                            for sub_field in line_fields_ids.sorted(key=lambda l: l.sequence):
                                if sub_field.v2line_field.ttype in ["many2one"]:
                                    sub_filed_val[sub_field.v2line_field.name] = rec[sub_field.v2line_field.name].id
                                else:
                                    sub_filed_val[sub_field.v2line_field.name] = rec[sub_field.v2line_field.name]
                            records.append(sub_filed_val)
                        value = records

    elif field.ttype in ["binary"]:
        ftype = "file"
    elif field.ttype in ["boolean"]:
        ftype = "checkbox"

    if field.ttype not in ["one2many","many2one"]:
        if logspace_request:
            if field.model_id.model == stepper.stepper_model_id.model:
                if logspace_request[field.name]:
                    value = logspace_request[field.name]
                    if logspace_request.state in ["draft","sent"]:
                        disabled = False
                    else:
                        disabled = True
        else:
            if stepper.stepper_model_id.model == 'res.partner':
                if partner_id:
                    family = request.env['res.partner'].sudo().browse(partner_id)
                    if family:
                        # if field.relation == stepper.stepper_model_id.model:
                        if field.model_id.model == stepper.stepper_model_id.model:
                            if family[field.name]:
                                value = family[field.name]
                                if family.allow_editing_portal:
                                    disabled = False
                                else:
                                    disabled = True

                                #Remove default name after new user registeration
                                if family.name == "Father Name":
                                    value = ""
                                    disabled = False
            
    return {
        "name":field.name,
        "label":field.field_description,
        "value":value,
        "type":ftype,
        "domain":"",
        "x2m_fields":x2m_fields,
        "disabled":disabled,
        "checked":False,
        "readonly":False,
        "required":False,
        "tip":field.help,
        "options":options,
    }