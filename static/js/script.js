document.getElementById("uploadForm").addEventListener("submit", function (e) {
  e.preventDefault();

  const fileInput = document.querySelector('#uploadForm input[type="file"]');
  if (!fileInput.files.length) {
      document.getElementById("errorFeedback").innerText = "Please select a video file to upload.";
      return; // Stop the function if no file is selected
  }

  const formData = new FormData(this);
  const preferences = Array.from(
      document.querySelectorAll('#uploadForm input[name="preference"]:checked')
  )
  .map((checkbox) => checkbox.value)
  .join(",");
  formData.append("preference", preferences); // Append preferences as a single string

  // Get the value of every_n_frame from the input and append it to FormData
  const everyNFrame = document.getElementById('singleEveryNFrame').value;
  formData.append('every_n_frame', everyNFrame);

  document.getElementById("feedback").innerText = "Processing... Please wait.";
  document.getElementById("errorFeedback").innerText = ""; // Clear previous error messages
  document.getElementById("downloads").innerHTML = ""; // Clear previous download links

  fetch("/upload_and_track/", {
      method: "POST",
      body: formData,
  })
  .then((response) => response.json())
  .then((data) => {
      console.log(data); // Logging the data for debugging
      if (data.status === "Animals detected" || data.status === "No animals detected") {
          const downloadsDiv = document.getElementById("downloads");
          Object.entries(data.paths).forEach(([key, value]) => {
              if (value) {
                  // Only display links for generated and kept files
                  const linkEl = document.createElement("a");
                  linkEl.href = value;
                  linkEl.textContent = `Download ${
                      key.replace("Url", "").charAt(0).toUpperCase() +
                      key.replace("Url", "").slice(1).replace(/_/g, " ")
                  }`;
                  linkEl.download = ""; // This attribute is not necessary for the link to work, but included for completeness
                  downloadsDiv.appendChild(linkEl);
                  downloadsDiv.appendChild(document.createElement("br")); // Add a line break between links
              }
          });
      } else {
          document.getElementById("errorFeedback").innerText = data.message || "An unexpected error occurred.";
      }
  })
  .catch((error) => {
      console.error("Error:", error);
      document.getElementById("errorFeedback").innerText = "An error occurred during the process. Please try again.";
  })
  .finally(() => {
      document.getElementById("feedback").innerText = ""; // Clear the processing message
  });
});





document.addEventListener('DOMContentLoaded', function() {
    const uploadMultipleForm = document.getElementById('uploadMultipleForm');

    let isSubmitting = false;

    function handleFormSubmit(e) {
        e.preventDefault();
        if (isSubmitting) {
            console.log("Submission is already in progress");
            return;
        }
        isSubmitting = true;
        console.log("Form submission started");

        const formData = new FormData(uploadMultipleForm);  // Directly pass the form
        const preferences = Array.from(document.querySelectorAll('#uploadMultipleForm input[name="preference"]:checked'))
                                .map(input => input.value)
                                .join(",");
        formData.append("preference", preferences);

        // Retrieve every_n_frame value and append it to formData
        const everyNFrame = document.getElementById('multipleEveryNFrame').value;
        formData.append('every_n_frame', everyNFrame);

        console.log(`Preferences selected: ${preferences}`);
        console.log(`Processing every ${everyNFrame} frames`);

        submitFormData(formData);
    }

    function submitFormData(formData) {
        fetch("/upload_and_track_multiple/", {
            method: "POST",
            body: formData,
        }).then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        }).then(data => {
            console.log("Response data received:", data);
            document.getElementById('multipleFeedback').textContent = "Processing complete. Download will start shortly.";
            // Automatically trigger the download
            triggerAutomaticDownload(data.session_id);
        }).catch(error => {
            console.error("Error during form submission:", error);
            document.getElementById('multipleErrorFeedback').textContent = "An error occurred. Please try again.";
        }).finally(() => {
            isSubmitting = false;
            console.log("Form submission ended");
        });
    }

    function triggerAutomaticDownload(sessionId) {
        const downloadUrl = `/zip/download/${sessionId}`;
        console.log("Triggering automatic download for session:", sessionId);
        window.location.href = downloadUrl; // This will trigger the download automatically.
    }

    uploadMultipleForm.addEventListener('submit', handleFormSubmit);
});




