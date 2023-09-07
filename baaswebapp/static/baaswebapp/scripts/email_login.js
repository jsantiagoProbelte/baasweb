console.log("email loaded")
const login_buttons = document.getElementById("login_buttons")
const email_form = document.getElementById("email_form")
const code_form = document.getElementById("code_form")
var email = ""

function activateEmail(){
  login_buttons.style.setProperty('display', 'none', 'important')
  email_form.style.display = ''
}

async function activateCode(csrf){
  email = document.getElementById('email').value
  console.log(email)
  email_form.style.display = 'none'
  code_form.style.display = ''

  const response = await fetch("/auth/email/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      // 'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: JSON.stringify({"email": email})
  });
  console.log(response.json()); // parses JSON response into native JavaScript objects
}

async function signIn(){
  const code = document.getElementById('code').value

  const response = await fetch("/auth/token/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      // 'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: JSON.stringify({"email": email, "token": code})
  });
  console.log(response.json()); // parses JSON response into native JavaScript objects
}