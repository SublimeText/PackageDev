$here = $MyInvocation.MyCommand.Definition
$here = split-path $here -parent
$root = resolve-path (join-path $here "..")

push-location $root
	if (-not (test-path (join-path $root "Doc"))) {
		new-item -itemtype "d" -name "Doc" > $null
	}
	push-location ".\Doc"
		get-childitem "..\*.rst" | foreach-object {
									& "rst2html.py" `
													"--template" "..\html_template.txt" `
													"--link-stylesheet" `
													"--stylesheet-path" "main.css" `
													$_.fullname "$($_.basename).html"
								}
	pop-location
	remove-item ".\MANIFEST" -erroraction silentlycontinue
	& ".\setup.py" "spa"
	(get-item ".\dist\AAAPackageDev.sublime-package").fullname | clip.exe
pop-location

start-process "https://bitbucket.org/guillermooo/aaapackagedev/downloads"