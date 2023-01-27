function scrollTo(target) {
    var scrollSpeed = 600;
    // Offset anchor location only since navigation bar is now static
    var offset = $(target).offset().top;
    $('html, body').animate({scrollTop:offset}, scrollSpeed);
};

var setDataPointAPI = '/set_data_point';

function processEnter(event,element) {
    var code = event.keyCode || event.which;
    if(code==13){
        // Cancel the default action, if needed
        result = setDataPoint(element);
        nextElement = element.parent().parent().parent().next().find('input.data-input-template');
        if (nextElement.length !== 0)
            nextElement.focus();
        else
            scrollTo('.baas-graphs');
        return result;
    }
}

function setDataPoint(element) {
    var formElement=element.parent()
    var dataJson={}
    $(element.serializeArray()).each(function(index,obj){
        dataJson[obj.name]=obj.value;
    });
    dataJson['data_point_id']=formElement.attr('id');

    $.ajax({
        type : formElement.attr('method'), 
        url: setDataPointAPI,
        data: dataJson,
        
        success: function(data){
            element.css("background-color", "grey");
        },
    
        failure: function() {
            alert('Error. Please reload');
        }
    });
    return false;
};


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


