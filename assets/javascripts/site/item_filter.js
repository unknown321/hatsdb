  function find_item(text)
  {
    $("#items").undelegate();
    $("#items").show()
    $('#items').empty()
    $("#items").append("<div class='three columns centered'><img src='/media/images/ajax-loader.gif'></div><br>")
    game_type = $('body').attr('game_type')
    if (game_type == 'tournament')
      game_type = 'dota2'
    Dajaxice.mongobase.filter_item_ajax(Dajax.process,{'text':$("#filter").val(), "game_type":game_type})
    $("#items").delegate("#aa", "click", blabla);
  }

  function select_item(defindex)
  {
    $('[item_selected=true]').css("background","transparent")
    $('[item_selected=true]').attr("onmouseover","this.style.backgroundColor='#bbbbbb';" )
    $('[item_selected=true]').attr("onmouseout","this.style.background='transparent';")
    $("#defindex").val(defindex)
    itemname = 'item_'+defindex
    $('[name='+itemname+']').removeAttr("onmouseover")
    $('[name='+itemname+']').removeAttr("onmouseout")
    $('[name='+itemname+']').css("background","#708090")
    $('[name='+itemname+']').attr("item_selected","true")
    $('#filter').val($('[item_selected=true]').find('img').attr('alt'))
  }

  function blabla()
  {
    itemid = $(this).attr('name').substring(5)
    itemname = $(this).find('img').attr('alt')
    itempic = $(this).find('img').attr('src')
    nextStep(itemid,itemname,itempic)
  }