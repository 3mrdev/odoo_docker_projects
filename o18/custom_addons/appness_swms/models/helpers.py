import datetime
from odoo.exceptions import ValidationError
from odoo import _

def validate_documents(self,rec,is_service=False):
    required_doc_types_list = []
    required_doc_types = ""

    expired_documents_list = []
    expired_documents = ""

    required_expire = ""
    required_issuance = ""

    domain = []
    if is_service:
        domain.append(("type", "=", "service"))
    else:
        domain.append(("type", "!=", "service"))
        domain.append(("family_type", "=", rec.family_type))
        
    doc_types = self.env["swms.document.type"].sudo().search(domain) 
    for type in doc_types:
        
        document_expire_date = False
        document_issuance_date = False
        
        # Documents
        flag_found = False
        for document in rec.documents:
            if document.doc_type:
                if type.id == document.doc_type.id:
                    flag_found = True
                    document_expire_date = document.expire_date
                    document_issuance_date = document.issuance_date
                    today = datetime.date.today()  
                    # raise ValidationError(f"document_expire_date: {document_expire_date} is: {today > document_expire_date}")
                    if document_expire_date:
                        if today > document_expire_date:
                            
                            flag_not_updated = True
                            prev_old_doc = False
                            documents = rec.documents.filtered(lambda x: x.expire_date != False)
                            for old_doc in documents.sorted('expire_date'):
                                if old_doc.doc_type:
                                    if type.id == old_doc.doc_type.id:
                                        old_doc_expire_date = old_doc.expire_date
                                        old_doc_issuance_date = old_doc.issuance_date
                                        if old_doc_expire_date:
                                            if old_doc_expire_date > today:
                                                flag_not_updated = False
                                                if prev_old_doc:
                                                    prev_old_doc.is_archived = True
                                            else:
                                                prev_old_doc = old_doc
                                        else:
                                            flag_not_updated = False

                            if flag_not_updated:
                                document.is_expired = True
                                if not document.is_archived:

                                    today = datetime.date.today()
                                    max_issuance_days = datetime.timedelta(days=type.max_issuance_date)
                                    max_expire_days = datetime.timedelta(days=type.max_expire_date)
                                    max_issuance_date = today - max_issuance_days
                                    max_expire_date = today + max_expire_days

                                    expired_documents += _("Please Upload an updated ") + type.name + _(" Document") + "\n"
                                    expired_documents_list.append({
                                        "label":type.name or '',
                                        # "name":type.code or '',
                                        "description":type.description or '',
                                        "is_service":is_service,
                                        "member_name": False if is_service else (rec.name if rec.family_type == "member" else _("Father")),
                                        "member_id": False if is_service else rec.id,
                                        "is_mandatory":type.is_mandatory,
                                        "issuance_date_is_mandatory":type.issuance_date_is_mandatory,
                                        "issuance_date_is_visible":type.issuance_date_is_visible,
                                        "expire_date_is_visible":type.expire_date_is_visible,
                                        "expire_date_is_mandatory":type.expire_date_is_mandatory,
                                        "max_issuance_date":max_issuance_date,
                                        "max_expire_date":max_expire_date,
                                        "expire_date":document_expire_date,
                                        "issuance_date":document_issuance_date,
                                        "tip":"TIP", #TODO: add dynamic tip
                                        "disabled":False,
                                    })
        
        doc_types_flag = False

        if flag_found:
            if type.expire_date_is_mandatory:
                if not document_expire_date:
                    required_expire  += (f"In Document {type.name} : Expire Date is required ! \n")
            if type.issuance_date_is_mandatory:
                if not document_issuance_date:
                    required_issuance  += (f"In Document {type.name} : Issuance Date is required ! \n")
        else:
            
            if is_service:
                if rec.service.document_types:
                    for doc in rec.service.document_types:
                        if type.id == doc.id:
                            if type.is_mandatory:
                                doc_types_flag = True
                            # if type.is_orphan:
                            #     doc_types_flag = True
                            # if type.is_needy_family:
                            #     doc_types_flag = True
                            # if type.is_education:
                            #     doc_types_flag = True
            else:
                if type.is_mandatory:
                    doc_types_flag = True

                if type.is_marriage and rec.marital == 'married':
                    doc_types_flag = True
                if type.is_birth and rec.age < 18:
                    doc_types_flag = True
                if type.is_death and rec.marital == 'widower':
                    doc_types_flag = True
                if type.is_divorce and rec.marital == 'divorced':
                    doc_types_flag = True

                if rec.is_dead:
                    doc_types_flag = False

                for income in rec.income_sources:
                    if income.doc_type.id == type.id:
                        flag_income = True
                        for mydoc in rec.documents:
                            if mydoc.doc_type.id == type.id:
                                flag_income = False
                        
                        if flag_income:
                            doc_types_flag = True

                for obligation in rec.obligations:
                    if obligation.doc_type.id == type.id:
                        flag_obligation = True
                        for mydoc in rec.documents:
                            if mydoc.doc_type.id == type.id:
                                flag_obligation = False
                        
                        if flag_obligation:
                            doc_types_flag = True

                for property in rec.properties:
                    if property.doc_type.id == type.id:
                        flag_property = True
                        for mydoc in rec.documents:
                            if mydoc.doc_type.id == type.id:
                                flag_property = False
                        
                        if flag_property:
                            doc_types_flag = True

            if doc_types_flag:

                today = datetime.date.today()
                max_issuance_days = datetime.timedelta(days=type.max_issuance_date)
                max_expire_days = datetime.timedelta(days=type.max_expire_date)
                max_issuance_date = today - max_issuance_days
                max_expire_date = today + max_expire_days

                required_doc_types += _("Please Upload ") + type.name + _(" Document") + "\n"
                required_doc_types_list.append({
                    "label":type.name or '',
                    # "name":type.code or '',
                    "description":type.description or '',
                    "is_service":is_service,
                    "member_name": '' if is_service else (rec.name if rec.family_type == "member" else _("Father")),
                    "member_id": False if is_service else rec.id,
                    "is_mandatory":type.is_mandatory,
                    "issuance_date_is_mandatory":type.issuance_date_is_mandatory,
                    "expire_date_is_mandatory":type.expire_date_is_mandatory,
                    "issuance_date_is_visible":type.issuance_date_is_visible,
                    "expire_date_is_visible":type.expire_date_is_visible,
                    "max_issuance_date":max_issuance_date,
                    "max_expire_date":max_expire_date,
                    "tip":"TIP", #TODO: add dynamic tip
                    "disabled":False,
                })

    return {
        "types_list":required_doc_types_list,
        "types":required_doc_types,
        "expire":required_expire,
        "issuance":required_issuance,
        "expired_list":expired_documents_list,
        "expired":expired_documents,
    }
    