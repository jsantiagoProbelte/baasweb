// Delete product on click
$("#table-items").on('click', 'a[id^=delete-item-]', function(){
    var item_id = $(this).attr('id').split('-')[2];
    return delete_item(item_id);
});

// AJAX for deleting
function delete_item(item_id){
    if (confirm('are you sure you want to remove this item?')==true){
        $.ajax({
            url : manageItemEndPoint, // the endpoint
            type : "DELETE", // http method
            data : { 'item_id' : item_id }, // data sent with the delete request
            success : function(json) {
                // hide the post
                $('#item-'+item_id).hide(); // hide the post on success
                console.log("post deletion successful");
            },

            error : function(xhr,errmsg,err) {
                // Show an error
                $('#errors').html("<div class='alert-box alert radius' data-alert>"+
                "Oops! We have encountered an error. <a href='#' class='close'>&times;</a></div>"); // add error to the dom
                console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
            }
        });
    } else {
        return false;
    }
};