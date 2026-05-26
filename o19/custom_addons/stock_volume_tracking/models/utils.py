def cal_volume_total(self,line,qty):
    if line.volume_length and line.volume_width and line.volume_height:
        volume_1 = (line.volume_length or 0)
        volume_2 = (line.volume_length or 0) * (line.volume_width or 0)
        volume_3 = (line.volume_length or 0) * (line.volume_width or 0) * (line.volume_height or 0)
        total_volume1 = (volume_1 * qty)
        total_volume2 = (volume_2 * qty)
        total_volume3 = (volume_3 * qty)
        cubic_volume1 = total_volume1/1000000
        cubic_volume2 = total_volume2/1000000
        cubic_volume3 = total_volume3/1000000
        # volume_display = f"{line.volume_length}×{line.volume_width}×{line.volume_height}={volume}x{qty}={total_volume} {line.product_id.volume_uom_name}"
        volume_display = f"{cubic_volume1}/{cubic_volume2}/{cubic_volume3} {line.product_id.volume_uom_name}"

    else:
        volume_display = "0×0×0"
        volume_3 = 0
        total_volume3 = 0
    
    line.volume = volume_3
    line.volume_total = total_volume3
    line.volume_display = volume_display