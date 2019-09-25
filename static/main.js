function checkbox_changed(event) {
  let form = event.parentNode.parentNode;
  let formData = new FormData(form)
  fetch('/put?name='+encodeURIComponent(form.name), {
    method: 'PUT',
    body: formData,
  })
    .then(response => {
      if (response.ok) {
      } else {
        throw new Error('Something went wrong on the server.');
      }
    })
    .catch(error => alert('Error:'+error.message))
}
