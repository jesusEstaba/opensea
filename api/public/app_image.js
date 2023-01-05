const myWidget = cloudinary.createUploadWidget(
    {
        cloudName: 'dpwaxzhnx',
        uploadPreset: 'tkxeggub',
        autoMinimize: true,
        resourceType: 'image',
        maxImageWidth: 500,
        maxImageHeight: 500,
        styles: {
            palette: {
                window: "#202225",
                windowBorder: "#ffffff",
                tabIcon: "#ffffff",
                menuIcons: "#ffffff",
                textDark: "#ffffff",
                textLight: "#ffffff",
                link: "rgb(32, 129, 226)",
                action: "#FF620C",
                inactiveTabIcon: "rgb(32, 129, 226)",
                error: "#F44235",
                inProgress: "#FFFFFF",
                complete: "#FFFFFF",
                sourceBg: "#1f1e1e"
            },
            frame: {
                background: "rgba(0, 0, 0, 0.8)"
            }
        }
    },
    (error, result) => {
        if (!error && result && result.event === "success") {
            console.log("imagen cargada")
            document.getElementById("image").value = result.info.secure_url
        }
    }
);

document.getElementById("upload_widget").addEventListener(
    "click",
    function (element) {
        element.preventDefault();
        myWidget.open();
    }
);