document.addEventListener('DOMContentLoaded', event => {
    const clipboardButtons = document.querySelectorAll('.clipboard').forEach(clipboardButton => {
        clipboardButton.addEventListener('click', event => {
            try{
                const extractList = event.target.dataset.extractFrom.split(" ")
                const tooltipId = event.target.dataset.tooltipId
                console.log(extractList)
                copyParams(...extractList)
                confirmation(event.target, 0.5)
            }catch(error){
                console.error(error)
            }
        })
    })
})

function copyParams(...args) {
    const values = args.map(it => document.querySelector(it).innerText).join(", ")

    navigator.clipboard.writeText(values)
}

function confirmation(target, seconds){
    const neutralClipboard = 'bi-clipboard'
    const confirmationClipboard = 'bi-clipboard-check'
    const millis = seconds * 1000
    target.classList.remove(neutralClipboard)
    target.classList.add(confirmationClipboard)
    setTimeout(() => {
        target.classList.remove(confirmationClipboard)
        target.classList.add(neutralClipboard)
    }, millis)
}