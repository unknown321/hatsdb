  function hidetooltip()
  {
    tooltip = document.getElementById('tooltip')
    tooltip.style.display = 'none'
  }

  function load_some_items(game_type,item_id,quality_id,count)
  {
    $('#results'+quality_id).empty()
    $('#results'+quality_id).append('<tr><td colspan=11><center><img src="/media/images/ajax-loader.gif"></center></td></tr>')
    Dajaxice.mongobase.default_items_detail_ajax(Dajax.process,{'game_type':game_type,'item_id':item_id,'quality_id':quality_id,'item_count':count})
  }