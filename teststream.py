import vlc

test_url = 'https://rr2---sn-25ge7nzz.googlevideo.com/videoplayback?expire=1738244335&ei=jyybZ9KJKOnOp-oP-_P0yAI&ip=82.64.198.215&id=o-AE_6Y4eys6JB77HR4svi6X-6tlfZRj9q5V8yazvKIzWZ&itag=251&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&met=1738222735%2C&mh=X-&mm=31%2C29&mn=sn-25ge7nzz%2Csn-25glenlz&ms=au%2Crdu&mv=m&mvi=2&pl=20&rms=au%2Cau&gcr=fr&initcwndbps=3040000&bui=AY2Et-M-6tzWNSeGuSg8CgM7xvCmj9d-7iT0Q1_fJAr0KnJflnmYWFcAc4CrAEsmB4r2VXmI3ubO4xZd&spc=9kzgDboXWImLKddzZH0umwh_psmyyflNbD0Eovm7lqNbq48QN11Uxjccew&vprv=1&svpuc=1&mime=audio%2Fwebm&ns=WY73ENrlX05J0dvCAQ7OuWkQ&rqh=1&gir=yes&clen=3786183&dur=222.801&lmt=1714513186152329&mt=1738222371&fvip=3&keepalive=yes&lmw=1&fexp=51326932%2C51371294&c=TVHTML5&sefc=1&txp=5432434&n=KBs5jXbMH63BMQ&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Cgcr%2Cbui%2Cspc%2Cvprv%2Csvpuc%2Cmime%2Cns%2Crqh%2Cgir%2Cclen%2Cdur%2Clmt&lsparams=met%2Cmh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Crms%2Cinitcwndbps&lsig=AGluJ3MwRQIhAM03CQHtM4YEMUPVhpu2SeL2-vzAXJRVKzR8yN1IjRYcAiB7XsDxk-OT6RnrERvmSNd545Fe9ul20k8cMpWU8bgAdQ%3D%3D&sig=AJfQdSswRAIgUH9edDU4xFzLo7t_Rdd_aCAAXUBXeAwiyokT7s8MxLICID2HSNEljItwbh_vinT23lFoeHwLRGeyJzM-lV7SAsEZ'

p = vlc.MediaPlayer(test_url)
p.play()
input("press enter to quit")
p.stop()
