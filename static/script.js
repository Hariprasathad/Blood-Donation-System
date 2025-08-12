        document.getElementById("donorForm").addEventListener("submit", function(event) {
            event.preventDefault();

            const formData = new FormData(this);

            fetch("/add_donor", {
                method: "POST",
                body: formData
            })
            .then(res => res.text())
            .then(data => alert(data))
        });