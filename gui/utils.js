function getAllChildren(obj,condition=function(o) { return true; }, level=0)
{
    //let objtype = "";
    //objtype += obj;  // Force object type to be string
    //if(objtype.indexOf("Tab_") == 0) obj.active = true; // Enforce it to be really loaded, and therefore have a non-zero length of children
    if("active" in obj)
    {
        try { obj.active = true; } catch (err) {}
    }


    let msg = "";
    for(let k=0; k<level; ++k) msg += "  ";
    msg += obj;
    if("title" in obj) msg += " -- " + obj.title;
    else if("text" in obj) msg += " -- " + obj.text;
    //console.log(msg);

    let result = []
    if(typeof obj.contentItem !== 'undefined' && typeof obj.children === 'undefined') obj = obj.contentItem;

    for(let i=0; i<obj.children.length; ++i)
    {
        msg = "";
        for(let k=0; k<level+1; ++k) msg += "  ";
        msg += "Checking: ";
        msg += obj.children[i];
        if(condition(obj.children[i]))
        {
            result.push(obj.children[i]);
            msg += "[YES]";
        }
        else msg += "[NO]";
        //console.log(msg);

        result = result.concat(getAllChildren(obj.children[i],condition,level+1));
    }
    return result;
}

function setChildrenEnabled(obj, status, condition=function(o) { return ("factorySetting" in o) && o.factorySetting; })
{
    let children = getAllChildren(obj,condition);
    for(let i=0; i<children.length; ++i)
    {
        if("enabled" in children[i]) children[i].enabled = status;
        else apdcamMain.showError("this input does not have an 'enabled' flag");
    }
}

