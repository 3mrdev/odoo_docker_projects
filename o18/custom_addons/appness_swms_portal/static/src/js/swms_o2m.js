/** @odoo-module **/
// import { jsonrpc } from "@web/core/network/rpc_service";
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.MaterialRequest = publicWidget.Widget.extend({
    selector: "#wrap",
    events: {
        'click .add_new_o2m_record': '_onClick_add_new_o2m_record',
        'click .remove_line': '_onClickRemove_line',
    },
    /**
     * @override
     */
    start: function () {
        var def = this._super.apply(this, arguments);

        var $table = this.$el.find('.o2m_records')
        var $lines = 0;
        $table.find('.o2m_record').each(function(){
            $lines  += 1;
        });
        // if there are no lines, hide the table
        if ($lines == 0){
            $table.addClass('d-none');
        } else {
            $table.removeClass('d-none');
        }

        return def;
    },
    _onClick_add_new_o2m_record: function(ev){
        var $table = $(ev.target).parent().find('.o2m_records');
        
        // $table.find('.fa-edit');
        $table.removeClass('d-none');

        var $blank_line = $(ev.target).parent().find('.new_o2m_record');
        var $new_row = $blank_line.clone(true);
        // var $new_row = $('.new_o2m_record').clone(true);
        $new_row.removeClass('d-none');
        $new_row.removeClass('new_o2m_record');
        $new_row.addClass('o2m_record');
        $new_row.insertBefore($blank_line);
    },
    _onClickRemove_line: function(ev){
        $(ev.target).parent().parent().remove();
        var $table = this.$el.find('.o2m_records')
        var $lines = 0;
        $table.find('.o2m_record').each(function(){
            $lines  += 1;
        });
        // if there are no lines, hide the table
        if ($lines == 0){
            $table.addClass('d-none');
        }else{
            $table.removeClass('d-none');
        }
    },
});