% menu propre au GPI a mettre dans les figures dans matlab5
% Tapper GPImenu

AxMenu = uimenu('Label','GPI menu');
uimenu(AxMenu,'Label','Viewer','Callback','viewer');
uimenu(AxMenu,'Label','Grid','Callback','grid');
if(ishold)
	uimenu(AxMenu,'Label','Hold off','Callback','AxisCallback(4,0)');
else
	uimenu(AxMenu,'Label','Hold on','Callback','AxisCallback(4,0)');
end
uimenu(AxMenu,'Label','Clear','Callback','clf; GPImenu');
uimenu(AxMenu,'Label','Close','Callback','close clf');
