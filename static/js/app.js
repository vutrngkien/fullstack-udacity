const deleteVenue = (el => {
    const id = el.dataset.id
    if(!id) return
    fetch(`/venues/${id}`, {
        method: 'DELETE'
    })
})