  function get_owner_info(owner_id)
  {
    $('#'+owner_id).empty()
    $('#'+owner_id).append("<img src='/media/images/ajax-loader.gif>")
    Dajaxice.mongobase.owner_info_ajax(Dajax.process,{ 'game_type':$('body').attr('game_type'), 'owner_id':owner_id})
  }

  function is_available(item_id,defindex)
  {
    $('#'+item_id).empty()
    $('#'+item_id).attr('class','')
    $('#'+item_id).removeAttr('onClick')
    $('#'+item_id).append("<img src='/media/images/ajax-loader-circle.gif'>")
    Dajaxice.mongobase.still_available_ajax(Dajax.process,{ 'game_type':$('body').attr('game_type'), 'item_id':item_id,'defindex':defindex})
  }