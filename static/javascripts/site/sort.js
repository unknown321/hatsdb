function sort(text,to_sort)
  {
    if (to_sort)
      items = $("#"+to_sort).find("[id=item]")
    else
      items = $("#items").find(".item")
    if(text.length > 0)
    {
      $("[id='line']").hide()
      items.each( function(){
        if( ($(this).attr('id').toUpperCase().indexOf(text.toUpperCase()) >= 0) || ($(this).attr('name').toUpperCase().indexOf(text.toUpperCase()) >= 0) )
        {
          $(this).show()
	        locstring = location.href.replace('#','')
          if (locstring.substr(locstring.length - 6) == "items/")
          {
            $(this).css('height','200px')
            $(this).css('display','inline-block')
          }
        }
        else
          $(this).hide()
      })

    }
    else
    {
      $("[id='line']").show()
      items.each( function(){
        $(this).show()
      })
    }
  }

function filter_by(text)
{
 $('#filter').val(text)
 sort(text)
}

