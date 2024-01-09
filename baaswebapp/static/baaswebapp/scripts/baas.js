function scrollTo(target) {
    var scrollSpeed = 600;
    // Offset anchor location only since navigation bar is now static
    var offset = $(target).offset().top;
    $('html, body').animate({scrollTop:offset}, scrollSpeed);
};



function processEnter(event,element, url, theId) {
    var code = event.keyCode || event.which;
    if(code==13){
        // Cancel the default action, if needed
        result = setDataPoint(element, url);
        nextElement = element.parent().parent().parent().next().find('input.'+theId);
        if (nextElement.length !== 0)
            nextElement[0].focus();
        else
            location.reload();
        return result;
    }
};


function setDataPoint(element, url) {
    var formElement=element.parent()
    var dataJson={}
    $(element.serializeArray()).each(function(index,obj){
        dataJson[obj.name]=obj.value;
    });
    dataJson['data_point_id']=formElement.attr('id');

    $.ajax({
        type : formElement.attr('method'), 
        url: url,
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


function loadTrialContent(){
{
    // Loop through each dynamic div
        $('.trial-dynamic-content').each(function() {
            var divId = $(this).attr('id'); // Get the ID of the current div
            /* Id will be like trial-id-contentId */
            var items = divId.split('-');
            var contentType = items[2]
            var trialId = items[1]
            // Make an AJAX call to the Django server
            $.ajax({
                type: 'GET',
                url: '/trial_content_api' ,  // Update with the actual URL
                data: { content_type: contentType, id: trialId }, // Send the div ID to the server
                success: function(response) {
                    // Update the content of the div with the loaded content
                    $('#' + divId).html(response);
                },
                error: function() {
                    // Handle error if the AJAX call fails
                    $('#' + divId).html('<p>Error loading content.</p>');
                }
            });
        });
    }
}


function loadAssessment(btn){
    var btnId = $(btn).attr('id'); // Get the ID of the current div
    /* Id will be like trial-id-contentId */
    var items = btnId.split('-');
    var assessmentId = items[3]
    var trialId = items[2]
    // Make an AJAX call to the Django server
    // See trial_assessment_view.html
    var divId = '#trial-'+ trialId + '-assessment_view'
    $.ajax({
        type: 'GET',
        url: '/trial_content_api' ,  // Update with the actual URL
        data: { content_type: "assessment_view", 
                id: trialId ,
                extra_id: assessmentId}, // Send the div ID to the server
        success: function(response) {
            // Update the content of the div with the loaded content
            $(divId).html(response);
        },
        error: function() {
            // Handle error if the AJAX call fails
            $(divId).html('<p>Error loading content.</p>');
        }
    });
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

function pasteData(event, setDataPointAPI) {
    event.preventDefault();
    const clipboardData = event.originalEvent.clipboardData || window.clipboardData;
    const pastedData = clipboardData.getData('text/plain').split('\n');

    // Get the active cell (where the user right-clicked or focused)
    const activeInput = document.activeElement;
    // Find the td parent
    //const activeCellID = activeCell.id;
    const activeCellID = activeInput.parentElement.parentElement.id;
    const [row, col] = activeCellID.split('-').slice(-2).map(Number);

    // Iterate through rows of pasted data
    for (let i = 0; i < pastedData.length; i++) {
        const rowData = pastedData[i].split('\t'); // Assuming tab-separated data
        
        // Iterate through columns of pasted data
        for (let j = 0; j < rowData.length; j++) {
            const cellID = `cell-${row + i}-${col + j}`;
            const cell = $(`#${cellID}`);
            
            if (cell.length) {
                const input = cell.find('input');
                if (input.length) {
                    const updatedValue = rowData[j];
                    // Update the input value locally
                    input.val(updatedValue);
                    // Perform AJAX update
                    setDataPoint(input, setDataPointAPI);
                }
            }
        }
    }
};

function copyColumnData(event){
    const target = event.currentTarget
    const column = target.dataset.column
    let rowCounter = 0
    let rowCell = document.querySelector(`#cell-${rowCounter}-${column}`)
    let string = ""

    while(rowCell){
        let value = rowCell.querySelector("input[type='text']").value
        value = value == "" ? "0.0" : value
        string += value
        string += "\n"

        rowCounter++
        rowCell = document.querySelector(`#cell-${rowCounter}-${column}`)
    }

    navigator.clipboard.writeText(string)
    const previousText = target.innerText
    target.innerText = "¡COPIADO!"
    target.classList.toggle("btn-danger")
    target.classList.toggle("btn-primary")
    setTimeout(() => {
        target.innerText = previousText
        target.classList.toggle("btn-danger")
        target.classList.toggle("btn-primary")
    }, 1000);
}

