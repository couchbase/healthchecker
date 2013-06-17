$(document).ready(function(){
    $("#report tr:odd").addClass("odd");
    $("#report tr:not(.odd)").hide();
    $("#report tr:first-child").show();
    $("#report tr.odd").click(function(){
        $(this).next("tr").toggle();
        $(this).find(".arrow").toggleClass("up");
    });
});
