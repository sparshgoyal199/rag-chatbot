let upload_url = "http://localhost:8000/upload"
let delete_url = "http://localhost:8000/session"

let upload_options = {
   method: 'POST'
}

let delete_options = {
   method: 'POST'
}

let query_form = document.getElementById("query_form")
let upload_form = document.getElementById("upload-form");
const decoder = new TextDecoder("utf-8")

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
   let session_id = sessionStorage.getItem("session_id")
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
      sessionStorage.setItem("session_id",session_id)
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
   let session_id = sessionStorage.getItem("session_id")
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

function render_query(query){

   let response_area = document.getElementById("response-area")

   let query_card = document.createElement("div")

   query_card.className =
      "flex justify-end"

   query_card.innerHTML = `
      <div class="bg-black text-white px-5 py-3 rounded-2xl max-w-2xl shadow">
         ${query}
      </div>
   `

   response_area.appendChild(query_card)

   response_area.scrollTop = response_area.scrollHeight
}

function create_streaming_response(){

   let response_area = document.getElementById("response-area")

   let response_wrapper = document.createElement("div")

   response_wrapper.className =
      "flex justify-start"

   response_wrapper.innerHTML = `
      <div class="bg-white border px-5 py-4 rounded-2xl max-w-4xl shadow-sm">

         <div class="text-xs font-semibold text-gray-500 mb-2">
            RAG Assistant
         </div>

         <p
            class="text-gray-800 whitespace-pre-wrap leading-7"
         >
         </p>

      </div>
   `

   response_area.appendChild(response_wrapper)

   response_area.scrollTop = response_area.scrollHeight

   return response_wrapper.querySelector("p")
}

function append_stream_chunk(response_element, chunk){

   response_element.textContent += chunk

   let response_area =
      document.getElementById("response-area")

   response_area.scrollTop =
      response_area.scrollHeight
}

function render_loader(){

   let response_area = document.getElementById("response-area")

   let loader_wrapper = document.createElement("div")

   loader_wrapper.id = "loader-bubble"

   loader_wrapper.className =
      "flex justify-start"

   loader_wrapper.innerHTML = `
      <div class="bg-white border px-5 py-4 rounded-2xl shadow-sm">

         <div class="flex gap-2 items-center">

            <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>

            <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.2s]"></div>

            <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.4s]"></div>

         </div>

      </div>
   `

   response_area.appendChild(loader_wrapper)

   response_area.scrollTop = response_area.scrollHeight
}

function remove_loader(){

   let loader = document.getElementById("loader-bubble")

   if(loader){
      loader.remove()
   }
}

async function augmented_answer(query_obj){
   const response = await fetch("http://localhost:8000/query",{
      method: "POST",
      body: JSON.stringify(query_obj),
      headers: {
         "Content-Type": "application/json"
      }
   })
   .then(resp => {
      if(!resp.ok) throw new Error(`Response status: ${resp.status}`);
      return resp
   })
   .catch(error => {
      remove_loader()
      alert(error.message)
   })

   remove_loader()

   const response_element = create_streaming_response()
   const reader = response.body.getReader()
   while(true){
      const chunk = await reader.read()
      const {done,value} = chunk
      if(done) break
      const decodedChunk = decoder.decode(value,{stream:true})
      if(decodedChunk == "done") break
      append_stream_chunk(response_element,decodedChunk)
}
}

async function query_document(event){
   event.preventDefault()
   let query = event.target.query.value
   event.target.query.value = ""
   if(query == "" || query == undefined || query == null){
      alert("Please provide the query!!")
      return
   }
   let session_id = sessionStorage.getItem("session_id")
   if (session_id == null || session_id == undefined) {
      alert("Please upload your doc first before querying...")
      return
   }
   let query_obj = {
      "query":query,
      "session_id":session_id
   }
   render_query(query)
   render_loader()
   await augmented_answer(query_obj)
}

upload_form.addEventListener("submit",upload_document)
query_form.addEventListener("submit",query_document)

// window.addEventListener("beforeunload", (event) => {
//     event.preventDefault();
//     event.returnValue = '';
// });

// window.addEventListener("pagehide", (event) => {
//     if (!event.persisted) {
//          let session_id = sessionStorage.getItem("session_id")
//         sessionStorage.removeItem("session_id");
//         navigator.sendBeacon(`http://127.0.0.1:8000/session/${session_id}`)
//     }
// });