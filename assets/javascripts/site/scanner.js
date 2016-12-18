function send()
{	
  toggle_scan_button()
  $('#scanner_results').html('')
  stickyFooter()

  var uncraft_check = false
  var untrade_check = false
  var marketable_check = false
	
  var steam_ids = $('#steam_ids').val()
  $('#steam_ids').val('Scanning...')

  if ($('#uncraft').attr('checked') == 'checked')
    uncraft_check = true

  if ($('#untrade').attr('checked') == 'checked')
    untrade_check = true    

  if ($('#marketable').attr('checked') == 'checked')
    marketable_check = true    

  var game_type = $('#gametypebuttons').find('.maintype').attr('id')

  Dajaxice.mongobase.scanner_results_ajax(Dajax.process,{'steam_ids':steam_ids, 
    'marketable_check':marketable_check,
    'uncraft_check':uncraft_check, 
    'untrade_check':untrade_check, 
    'game_type':game_type})  
}

function switch_game(game)
{
  var buttons = $('#gametypebuttons').find('.radius')
  buttons.each(function(){$(this).attr('class',"radius label secondary")})
  $('#' + game).attr('class',"radius label maintype")
}


function toggle_visibility(steam_id)
{ 
  $('#'+steam_id).toggle()
}

 
function toggle_scan_button()
{
  $('#scan_button').text('')
  $('#scan_button').attr('disabled','disabled')
  $('#scan_button').append('<img src="/static/images/ajax-loader-circle.gif">')
}

function filter_items()
{
  game_type = $('#gametypebuttons').find('.maintype').attr('id')
  item_name = $("[id='right-label filter']").val()
  filter = "item_wrapper_"+game_type
  pattern = RegExp(item_name,'i')
  all_items = $('#scanner_results').find("[class$="+filter+"]")
  toshow = $.grep(all_items, function (el) 
  {
    if ($(el).attr('info').match(pattern))
      return el
  })
  $(all_items).each(function(){$(this).fadeTo(0,0.3)})
  $(toshow).each(function(){$(this).fadeTo(0,1)})
}

function clear_filter()
{
  game_type = $('#gametypebuttons').find('.maintype').attr('id')
  filter = "item_wrapper_"+game_type
  $('#scanner_results').find("[class$="+filter+"]").each(function(){$(this).fadeTo(0,1)})
  $('#filter').val("")
}

// adds item description on click
function add_notification(item)
{
  iid = $(item).attr('id')
  notification_row = $("[id=n_"+iid+"]")
  if ($(notification_row).length > 0)
    {
      $(notification_row).remove()
      $(item).removeClass('selected_item_pic')
    }
  else
    {  
      $(item).addClass('selected_item_pic')
      parent = $(item).parent()
      notification_row = $("<div class='row item_info'></div>").insertAfter(parent)
      $(notification_row).html($(item).attr('info'))
      $(notification_row).attr('id','n_' + iid)
      $(notification_row).append('<p class="hide_info">×</p>')

      $('[class=hide_info]').click(
        function ()
        {
          p = $(this).parent()
          iid = ($(p).attr('id')).substr(2)
          item = $('#'+iid)
          $(item).removeClass('selected_item_pic')
          $(p).remove()
        }
      )
    }
}

function switch_box(item){
  // thanks foundation faggots, it is impossible to check if checkbox is checked with your faggot scripts
  if ($(item).attr("checked") == "checked")
      $(item).removeAttr("checked")
    else
      $(item).attr("checked","checked")
}

function check_for_results()
{
  task_ids = ($('#tasks').val()).split(',')
  game_type = $('#gametypebuttons').find('.maintype').attr('id')
  $(task_ids).each(function get(key, value){
    Dajaxice.mongobase.send_data_ajax(Dajax.process,
           {'task_id':value,'game_type':game_type, task_type:'scanner'});
    $('#scanner_results').append('<div class="row" id="'+value+'"><div class="large-1 columns large-centered end"><center><img src="/static/images/ajax-loader-circle.gif"></br><center></div></div>')
  })
}