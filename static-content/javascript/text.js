/* js for the text/essays pages */
$(function(){
	$('a.thickbox img').each(function(){
		$(this).parent().attr('href', this.src.replace('_thum.jpg', '_full.jpg'));
	})
})