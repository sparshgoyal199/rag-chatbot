let upload_form = document.getElementById("upload-form");
let upload_url = "http://localhost:8000/upload"
let delete_url = "http://localhost:8000/session"

let upload_options = {
   method: 'POST'
}

let delete_options = {
   method: 'DELETE'
}

let query_form = document.getElementById("query_form")


function session_status_update(){
   let session_status = document.getElementById("session_status")
   session_status.innerText = "Session is now active"
}

function start_loader() {
   let upload_btn = document.getElementById("upload-btn")

   upload_btn.disabled = true
   upload_btn.innerText = "Processing..."
   upload_btn.classList.add("opacity-70", "cursor-not-allowed")
}

function stop_loader() {
   let upload_btn = document.getElementById("upload-btn")

   upload_btn.disabled = false
   upload_btn.innerText = "Ingest Document"
   upload_btn.classList.remove("opacity-70", "cursor-not-allowed")
}

async function delete_collection(){
   let session_id = localStorage.getItem("session_id")
   return await fetch(`${delete_url}/${session_id}`,delete_options)
      .then((resp) =>
            {if (!resp.ok){
               throw new Error(`Response status: ${resp.status}`)
            }
            return true
         }
      )
      .catch(error => {
         alert(error.message)
         return false
      })
}

async function upload_collection(formData){
   upload_options.body = formData
   await fetch(`${upload_url}`,upload_options)
   .then(resp => {
     if(!resp.ok){
        throw new Error(`Response status: ${resp.status}`);
     }
     return resp.json()
   })
   .then(data => {
      let session_id = data["session_id"]
      localStorage.setItem("session_id",session_id)
      session_status_update() 
   })
   .catch(error => {
      alert(error.message)
   })
   .finally(() => {
      stop_loader()
   })
}

async function upload_document(event){
   event.preventDefault()
   start_loader()
   let session_id = localStorage.getItem("session_id")
   if(session_id != undefined && session_id != null){
      let del_resp = await delete_collection()
      if(del_resp == false){
         stop_loader()
         return
      }
   }
   let file = event.target.file.files[0]
   let formData = new FormData()
   formData.append('file', file)
   await upload_collection(formData)
}

async function augmented_answer(query_obj){
   await fetch("http://localhost:8000/query",{
      method: "POST",
      body: JSON.stringify(query_obj),
      headers: {
         "Content-Type": "application/json"
      }
   })
   .then(resp => {
      if(!resp.ok) throw new Error(`Response status: ${resp.status}`);
      return resp.json()
   })
   .then(data => {
      let llm_resp = data["answer"]
      console.log(llm_resp);
   })
}

async function query_document(event){
   event.preventDefault()
   let query = event.target.query.value
   if(query == "" || query == undefined || query == null){
      alert("Please provide the query!!")
      return
   }
   let session_id = localStorage.getItem("session_id")
   let query_obj = {
      "query":query,
      "session_id":session_id
   }
   await augmented_answer(query_obj)
}

upload_form.addEventListener("submit",upload_document)
query_form.addEventListener("submit",query_document)
