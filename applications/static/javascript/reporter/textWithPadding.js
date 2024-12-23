fabric.TextboxWithPadding = fabric.util.createClass(fabric.Textbox, {
      type: "textbox",
      strokeWidth: 5, // Define stroke width
      strokeColor: "#ffb64f", // Define stroke color
      splitByGrapheme: true,
    
      rx: 0, // Define rx value for rounded corners on x-axis
      ry: 0, // Define ry value for rounded corners on y-axis
      toObject: function () {
        return fabric.util.object.extend(this.callSuper("toObject"), {
          backgroundColor: this.get("backgroundColor"),
          padding: this.get("padding"),
          splitByGrapheme: this.get("splitByGrapheme"),
          rx: this.get("rx"),
          ry: this.get("ry")
        });
      },
    
      _renderBackground: function (ctx) {
        if (!this.backgroundColor) {
          return;
        }
        var dim = this._getNonTransformedDimensions();
        ctx.fillStyle = this.backgroundColor;
        ctx.fillRect(
          -dim.x / 2 - this.padding,
          -dim.y / 2 - this.padding,
          dim.x + this.padding * 2,
          dim.y + this.padding * 2
        );
        // Add stroke only at the top
        ctx.strokeStyle = this.strokeColor;
        ctx.lineWidth = this.strokeWidth;
        ctx.beginPath();
        ctx.moveTo(-dim.x / 2 - this.padding, -dim.y / 2 - this.padding);
        ctx.lineTo(-dim.x / 2 - this.padding, dim.y / 2 + this.padding);
        ctx.stroke();
    
        ctx.beginPath();
        ctx.strokeStyle = this.strokeColor;
        ctx.lineWidth = 0.2; // Set line width to 1
        ctx.lineTo(dim.x / 2 + this.padding, -dim.y / 2 - this.padding + 1);
        ctx.lineTo(dim.x / 2 + this.padding, dim.y / 2 + this.padding - 1);
        ctx.strokeStyle = "#9181fc";
    
        ctx.lineWidth = 0.2; // Set line width to 1
        ctx.lineTo(dim.x / 2 + this.padding - 1, dim.y / 2 + this.padding);
        ctx.lineTo(-dim.x / 2 - this.padding + 1, dim.y / 2 + this.padding);
        ctx.strokeStyle = "#9181fc";
    
        ctx.lineWidth = 0.2; // Set line width to 1
        ctx.lineTo(-dim.x / 2 - this.padding, dim.y / 2 + this.padding - 1);
        ctx.lineTo(-dim.x / 2 - this.padding, -dim.y / 2 - this.padding + 1);
        ctx.closePath();
    
        ctx.stroke();
    
        // if there is background color no other shadows
        // should be casted
        this._removeShadow(ctx);
      }
    });