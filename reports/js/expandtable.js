$(document).ready(function(){
    $("table#report > tbody > tr:even").addClass("even");
    $("table#report > tbody > tr:odd").hide()
    $("table#report > tbody > tr.even").click(function(){
        $(this).next("tr").toggle();
       $(this).find(".arrow").toggleClass("up");
    });
});
