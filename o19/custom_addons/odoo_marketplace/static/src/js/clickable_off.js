/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { Message } from '@mail/core/common/message';
import { MessagingMenu } from '@mail/core/public_web/messaging_menu';
import { useState } from "@odoo/owl";
import { ActivityMenu } from '@mail/core/web/activity_menu';
import { DebugMenu } from "@web/core/debug/debug_menu";
import { user } from "@web/core/user";
import { Chatter } from "@mail/chatter/web_portal/chatter";
import { AvatarCardPopover } from "@mail/discuss/web/avatar_card/avatar_card_popover";


patch(AvatarCardPopover.prototype, {
    setup() {
        const res = super.setup();
        const self = this;
        this.seller_info = useState({ seller: false });

        user.hasGroup('odoo_marketplace.marketplace_officer_group').then(function(isSeller) {
            self.seller_info.seller = isSeller;
        });

        return res;
    },
});

patch(MessagingMenu.prototype,{
  setup(){
    var res = super.setup()
    var self = this
    this.state = useState({
            seller:true
        });
    var seller = user.hasGroup('odoo_marketplace.marketplace_officer_group')
    seller.then(function(data){
      Object.assign(self.state, { seller: data});
    })
    return res
  },
})

patch(Chatter.prototype,{
  setup(){
    var res = super.setup()
    var self = this
    this.state = useState({
            seller:true
        });
    var seller = user.hasGroup('odoo_marketplace.marketplace_officer_group')
    seller.then(function(data){
      Object.assign(self.state, { seller: data});
    })
    return res
  },
})

patch(DebugMenu.prototype,{
  setup(){
    var res = super.setup()
    var self = this
    this.state = useState({
            seller:true
        });
    var seller = user.hasGroup('odoo_marketplace.marketplace_officer_group')
    seller.then(function(data){
      Object.assign(self.state, { seller: data});
    })
    return super.setup()
  },
})

patch(ActivityMenu.prototype,{
  setup(){
    var res = super.setup()
    var self = this
    this.seller_info = useState({
            seller:true
        });
    var seller = user.hasGroup('odoo_marketplace.marketplace_officer_group')
    seller.then(function(data){
      Object.assign(self.seller_info, { seller: data});
    })
    return res
  }
})

patch(Message.prototype,{

  setup() {
    var res = super.setup()
    var self = this
    this.noseller = useState({
      noseller:true
        });
  var noseller = user.hasGroup('odoo_marketplace.marketplace_officer_group')
  noseller.then(function(data){
        self.noseller = data
      })
  this.noseller = self.noseller
  return res
},
onClick(ev) {
        if (!this.noseller){
          ev.preventDefault(); 
          return false
        }
        return super.onClick(ev)
    },
})    
